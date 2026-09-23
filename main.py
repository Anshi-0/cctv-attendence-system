import os
import cv2
import face_recognition
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from mtcnn.mtcnn import MTCNN
import warnings
import asyncio
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import json
import base64
from pydantic import BaseModel

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.xlsx")
UNKNOWN_FACES_DIR = os.path.join(BASE_DIR, "unknown_faces")

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(UNKNOWN_FACES_DIR, exist_ok=True)

OUT_TIME_GAP_HOURS = 7
MTCNN_CONFIDENCE_THRESHOLD = 0.9

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
detector = None
known_encodings = []
known_names = []
camera_active = False
camera = None

def load_known_faces():
    global known_encodings, known_names
    known_encodings = []
    known_names = []
    for file in os.listdir(KNOWN_FACES_DIR):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(file)[0]
            path = os.path.join(KNOWN_FACES_DIR, file)
            try:
                image = face_recognition.load_image_file(path)
                face_enc = face_recognition.face_encodings(image)
                if face_enc:
                    known_encodings.append(face_enc[0])
                    known_names.append(name)
            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {e}")

@app.on_event("startup")
async def startup_event():
    global detector
    print("Initializing MTCNN detector...")
    detector = MTCNN()
    print("Loading known faces...")
    load_known_faces()
    print("System ready.")

def convert_mtcnn_to_face_locations(detection):
    x, y, width, height = detection['box']
    top = max(0, y)
    left = max(0, x)
    bottom = y + height
    right = x + width
    return (top, right, bottom, left)

def mark_attendance(name: str):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    new_entry = {
        "Name": name,
        "Date": today_str,
        "Time": time_str,
        "Status": "IN"
    }

    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame([new_entry])
        df.to_excel(ATTENDANCE_FILE, index=False)
        return f"[IN] {name} → {time_str}"

    try:
        df = pd.read_excel(ATTENDANCE_FILE)
        if "Name" in df.columns:
            df["Name"] = df["Name"].astype(str)
        if "Date" in df.columns:
            df["Date"] = df["Date"].astype(str)

        today_rows = df[
            (df["Name"].str.lower() == name.lower()) &
            (df["Date"] == today_str)
        ]

        if len(today_rows) == 0:
            new_df = pd.DataFrame([new_entry])
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_excel(ATTENDANCE_FILE, index=False)
            return f"[IN] {name} → {time_str}"
        elif len(today_rows) == 1:
            in_time_str = str(today_rows.iloc[0]["Time"])
            try:
                in_datetime = datetime.strptime(f"{today_str} {in_time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                in_datetime = now

            time_gap = now - in_datetime
            if time_gap >= timedelta(hours=OUT_TIME_GAP_HOURS):
                new_entry["Status"] = "OUT"
                new_df = pd.DataFrame([new_entry])
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_excel(ATTENDANCE_FILE, index=False)
                return f"[OUT] {name} → {time_str}"
    except Exception as e:
        print(f"[ERROR] Attendance marking error: {e}")
    return None


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/camera/start")
def start_camera():
    global camera_active, camera
    if not camera_active:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        camera_active = True
    return {"status": "started"}

@app.post("/api/camera/stop")
def stop_camera():
    global camera_active, camera
    if camera_active:
        camera_active = False
        if camera:
            camera.release()
            camera = None
    return {"status": "stopped"}

@app.get("/api/camera/status")
def camera_status():
    global camera_active
    return {"active": camera_active}

@app.get("/api/persons")
def get_persons():
    persons = []
    for f in os.listdir(KNOWN_FACES_DIR):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            persons.append({"id": f, "name": os.path.splitext(f)[0]})
    return persons

@app.post("/api/persons/register")
async def register_person(name: str, file: UploadFile = File(...)):
    path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    load_known_faces()
    return {"status": "success", "name": name}

@app.delete("/api/persons/{id}")
def delete_person(id: str):
    path = os.path.join(KNOWN_FACES_DIR, id)
    if os.path.exists(path):
        os.remove(path)
        load_known_faces()
    return {"status": "deleted"}

@app.get("/api/attendance")
def get_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        return []
    df = pd.read_excel(ATTENDANCE_FILE)
    df.fillna('', inplace=True)
    return df.to_dict(orient="records")

@app.get("/api/attendance/today")
def get_attendance_today():
    if not os.path.exists(ATTENDANCE_FILE):
        return []
    df = pd.read_excel(ATTENDANCE_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    today_df = df[df["Date"].astype(str) == today]
    today_df.fillna('', inplace=True)
    return today_df.to_dict(orient="records")

@app.get("/api/attendance/stats")
def get_attendance_stats():
    total_registered = len(known_names)
    present_today = 0
    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_excel(ATTENDANCE_FILE)
        today = datetime.now().strftime("%Y-%m-%d")
        present_today = len(set(df[df["Date"].astype(str) == today]["Name"]))
    unknown_count = len([f for f in os.listdir(UNKNOWN_FACES_DIR) if f.endswith(".jpg")])
    return {
        "registered": total_registered,
        "presentToday": present_today,
        "unknownDetects": unknown_count
    }

@app.get("/api/attendance/export")
def export_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=["Name", "Date", "Time", "Status"])
        df.to_excel(ATTENDANCE_FILE, index=False)
    return FileResponse(ATTENDANCE_FILE, filename="attendance.xlsx")

@app.get("/api/unknown-faces")
def get_unknown_faces():
    faces = []
    for f in os.listdir(UNKNOWN_FACES_DIR):
        if f.lower().endswith(".jpg"):
            path = os.path.join(UNKNOWN_FACES_DIR, f)
            with open(path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                faces.append({"id": f, "image": f"data:image/jpeg;base64,{encoded_string}", "timestamp": f.replace("unknown_", "").replace(".jpg", "")})
    return faces

class LiveRegisterRequest(BaseModel):
    name: str
    image: str

@app.post("/api/persons/register-live")
async def register_live_person(req: LiveRegisterRequest):
    img_data = req.image.split(",")[1] if "," in req.image else req.image
    path = os.path.join(KNOWN_FACES_DIR, f"{req.name}.jpg")
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(img_data))
    load_known_faces()
    return {"status": "success", "name": req.name}

@app.delete("/api/unknown-faces/{id}")
def delete_unknown_face(id: str):
    path = os.path.join(UNKNOWN_FACES_DIR, id)
    if os.path.exists(path):
        os.remove(path)
    return {"status": "deleted"}

@app.delete("/api/unknown-faces")
def clear_all_unknown_faces():
    for f in os.listdir(UNKNOWN_FACES_DIR):
        if f.lower().endswith(".jpg"):
            path = os.path.join(UNKNOWN_FACES_DIR, f)
            os.remove(path)
    return {"status": "cleared"}

class RegisterUnknownRequest(BaseModel):
    name: str

@app.post("/api/unknown-faces/register/{id}")
def register_unknown_face(id: str, req: RegisterUnknownRequest):
    old_path = os.path.join(UNKNOWN_FACES_DIR, id)
    if os.path.exists(old_path):
        new_path = os.path.join(KNOWN_FACES_DIR, f"{req.name}.jpg")
        shutil.move(old_path, new_path)
        load_known_faces()
        return {"status": "success", "name": req.name}
    return {"status": "error", "message": "File not found"}


@app.websocket("/ws/camera")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global camera_active, camera, detector, known_encodings, known_names
    
    frame_count = 0
    detection_interval = 5
    
    try:
        while True:
            if not camera_active or camera is None:
                await asyncio.sleep(0.5)
                continue
                
            ret, frame = camera.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue
                
            frame_count += 1
            boxes = []
            
            if frame_count % detection_interval == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detections = detector.detect_faces(rgb_frame)
                
                for detection in detections:
                    if detection['confidence'] < MTCNN_CONFIDENCE_THRESHOLD:
                        continue
                        
                    top, right, bottom, left = convert_mtcnn_to_face_locations(detection)
                    face_region = frame[max(0, top):bottom, max(0, left):right]
                    
                    if face_region.size == 0:
                        continue
                        
                    try:
                        rgb_face_region = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
                        face_enc = face_recognition.face_encodings(rgb_face_region, [(0, face_region.shape[1], face_region.shape[0], 0)])
                        
                        name = "Unknown"
                        if face_enc:
                            enc = face_enc[0]
                            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.6)
                            distances = face_recognition.face_distance(known_encodings, enc)
                            if len(distances) > 0:
                                best_index = distances.argmin()
                                if matches[best_index]:
                                    name = known_names[best_index]
                                    mark_attendance(name)
                            
                            if name == "Unknown":
                                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                path = os.path.join(UNKNOWN_FACES_DIR, f"unknown_{stamp}.jpg")
                                cv2.imwrite(path, face_region)
                        
                        boxes.append({
                            "left": left,
                            "top": top,
                            "width": right - left,
                            "height": bottom - top,
                            "name": name,
                            "confidence": float(detection['confidence'])
                        })
                    except Exception as e:
                        pass
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            b64_frame = base64.b64encode(buffer).decode('utf-8')
            
            await websocket.send_json({
                "type": "frame",
                "image": b64_frame,
                "boxes": boxes,
                "width": frame.shape[1],
                "height": frame.shape[0]
            })
            
            await asyncio.sleep(0.03) # roughly 30 fps
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WS error: {e}")
