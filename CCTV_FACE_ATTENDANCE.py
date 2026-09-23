import os
import cv2
import face_recognition
import pandas as pd
from datetime import datetime, timedelta
import winsound
import numpy as np
from mtcnn.mtcnn import MTCNN
import warnings
from typing import List, Tuple, Dict, Optional

warnings.filterwarnings('ignore')

KNOWN_FACES_DIR = r"C:\Users\Keyur Trivedi\CCTV_Attendance\known_faces"
ATTENDANCE_FILE = r"C:\Users\Keyur Trivedi\CCTV_Attendance\attendance.xlsx"
UNKNOWN_FACES_DIR = r"C:\Users\Keyur Trivedi\CCTV_Attendance\unknown_faces"

OUT_TIME_GAP_HOURS = 7
MTCNN_CONFIDENCE_THRESHOLD = 0.9  # Minimum confidence for face detection


def alert_sound() -> None:
    """Generate a beep sound alert."""
    try:
        winsound.Beep(1000, 400)
    except Exception:
        pass


def load_known_faces() -> Tuple[List[np.ndarray], List[str]]:
    """
    Load known faces and their encodings using face_recognition (dlib-based).
    Returns: Tuple of (encodings list, names list)
    """
    encodings: List[np.ndarray] = []
    names: List[str] = []

    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        print("[INFO] Created known_faces folder.")
        return encodings, names

    for file in os.listdir(KNOWN_FACES_DIR):

        if file.lower().endswith((".jpg", ".jpeg", ".png")):

            name = os.path.splitext(file)[0]

            path = os.path.join(KNOWN_FACES_DIR, file)

            try:
                image = face_recognition.load_image_file(path)

                face_enc = face_recognition.face_encodings(image)

                if face_enc:
                    encodings.append(face_enc[0])
                    names.append(name)
                    print(f"[INFO] Loaded face for: {name}")

                else:
                    print(f"[WARN] No detectable face in: {file}")

            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {str(e)}")

    return encodings, names


def detect_faces_mtcnn(detector: MTCNN, frame: np.ndarray) -> List[Dict]:
    """
    Detect faces using MTCNN detector.
    Returns list of detections with confidence scores and bounding boxes.
    
    MTCNN output format:
    {'box': [x, y, width, height], 'confidence': 0.99, 'keypoints': {...}}
    """
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = detector.detect_faces(rgb_frame)
        
        # Filter detections by confidence threshold
        valid_detections = [d for d in detections if d['confidence'] >= MTCNN_CONFIDENCE_THRESHOLD]
        
        return valid_detections
    
    except Exception as e:
        print(f"[WARN] MTCNN detection error: {str(e)}")
        return []


def convert_mtcnn_to_face_locations(detection: Dict) -> Tuple[int, int, int, int]:
    """
    Convert MTCNN detection format to face_recognition format.
    
    MTCNN: {'box': [x, y, width, height], ...}
    face_recognition format: (top, right, bottom, left)
    
    Returns: Tuple of (top, right, bottom, left) coordinates
    """
    x, y, width, height = detection['box']
    
    # Ensure coordinates are within valid range
    top = max(0, y)
    left = max(0, x)
    bottom = y + height
    right = x + width
    
    return (top, right, bottom, left)


def mark_attendance(name: str) -> Optional[str]:
    """
    Mark attendance for a person.
    Returns status message if attendance is recorded, None otherwise.
    """

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

                in_datetime = datetime.strptime(
                    f"{today_str} {in_time_str}",
                    "%Y-%m-%d %H:%M:%S"
                )

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
        print(f"[ERROR] Attendance marking error: {str(e)}")

    return None


def draw_dashboard(frame: np.ndarray, total_registered: int, present_today: int, detection_method: str = "MTCNN") -> None:
    """
    Draw dashboard information on the frame.
    """

    lines = [
        "CCTV Attendance System v2.0",
        f"Detection: {detection_method} | Recognition: dlib",
        f"Registered: {total_registered}",
        f"Present Today: {present_today}",
        "Press Q or ESC to Exit"
    ]

    y = 20

    for line in lines:

        cv2.putText(
            frame,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        y += 25


def main() -> None:
    """
    Main function to run the CCTV attendance system.
    """

    print("\n" + "="*60)
    print("MTCNN CCTV FACE RECOGNITION ATTENDANCE SYSTEM v2.0")
    print("="*60)

    print("\n[STEP] Initializing MTCNN detector...")
    
    try:
        # Initialize MTCNN detector - no TensorFlow required for inference
        detector = MTCNN()
        print("[INFO] ✓ MTCNN detector initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize MTCNN: {str(e)}")
        print("[INFO] Installation command: pip install mtcnn")
        print("[INFO] If still failing, try: pip install --upgrade mtcnn")
        return

    print("[STEP] Loading known faces...")

    known_encodings, known_names = load_known_faces()

    if not known_encodings:
        print("[ERROR] No known faces found.")
        print("[INFO] Please add face images to:", KNOWN_FACES_DIR)
        return

    print(f"[INFO] ✓ Loaded {len(known_names)} known faces")

    os.makedirs(UNKNOWN_FACES_DIR, exist_ok=True)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        print("[INFO] Please check if your webcam is connected.")
        return

    # Set webcam properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("\n[STEP] CCTV Attendance System Started")
    print(f"[INFO] Detection Confidence Threshold: {MTCNN_CONFIDENCE_THRESHOLD}")
    print("[INFO] Press Q or ESC to Exit\n")
    print("="*60 + "\n")

    frame_count = 0
    detection_interval = 2  # Process MTCNN every 2 frames for good balance

    try:
        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1

            present_today_count = 0

            if os.path.exists(ATTENDANCE_FILE):
                try:
                    df_att = pd.read_excel(ATTENDANCE_FILE)
                    today = datetime.now().strftime("%Y-%m-%d")
                    present_today_count = len(set(df_att[df_att["Date"] == today]["Name"]))
                except Exception as e:
                    print(f"[WARN] Error reading attendance file: {str(e)}")

            # Run MTCNN detection every Nth frame for performance optimization
            if frame_count % detection_interval == 0:
                
                detections = detect_faces_mtcnn(detector, frame)

                for detection in detections:
                    
                    top, right, bottom, left = convert_mtcnn_to_face_locations(detection)
                    
                    confidence = detection['confidence']

                    # Extract face region and encode with dlib
                    face_region = frame[max(0, top):bottom, max(0, left):right]

                    if face_region.size == 0:
                        continue

                    try:
                        rgb_face_region = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
                        
                        face_enc = face_recognition.face_encodings(
                            rgb_face_region,
                            [(0, face_region.shape[1], face_region.shape[0], 0)]
                        )

                        if not face_enc:
                            name = "Unknown"
                        else:
                            enc = face_enc[0]

                            matches = face_recognition.compare_faces(
                                known_encodings, enc, tolerance=0.6
                            )

                            distances = face_recognition.face_distance(known_encodings, enc)

                            name = "Unknown"

                            if len(distances) > 0:

                                best_index = distances.argmin()

                                if matches[best_index]:

                                    name = known_names[best_index]

                                    msg = mark_attendance(name)

                                    if msg:
                                        print(msg)

                            if name == "Unknown":
                                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                                path = os.path.join(
                                    UNKNOWN_FACES_DIR,
                                    f"unknown_{stamp}.jpg"
                                )

                                cv2.imwrite(path, face_region)
                                alert_sound()
                                print(f"[ALERT] Unknown face detected and saved: {stamp}")

                    except Exception as e:
                        print(f"[WARN] Error processing face: {str(e)}")
                        name = "Unknown"

                    # Draw bounding box
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    
                    cv2.rectangle(
                        frame,
                        (left, top),
                        (right, bottom),
                        color,
                        2
                    )

                    # Draw label with confidence
                    label_text = f"{name} ({confidence:.2f})"
                    
                    cv2.putText(
                        frame,
                        label_text,
                        (left, bottom + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                        cv2.LINE_AA
                    )

            draw_dashboard(
                frame,
                len(known_names),
                present_today_count,
                detection_method="MTCNN"
            )

            cv2.imshow("MTCNN Face Recognition CCTV Attendance", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                print("\n[INFO] Exiting system...")
                break

            try:
                if cv2.getWindowProperty("MTCNN Face Recognition CCTV Attendance", cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break

    except KeyboardInterrupt:
        print("\n[INFO] System interrupted by user")
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] ✓ System shutdown complete.")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()