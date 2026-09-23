# CCTV Face Attendance System

A real-time **CCTV Face Recognition Attendance System** that uses **MTCNN** for face detection and **dlib-based `face_recognition`** for face recognition.

The system provides a web dashboard for monitoring the camera, registering people, viewing attendance records, managing unknown faces, and exporting attendance data.

## Features

* 🎥 Real-time camera monitoring
* 👤 Face detection using **MTCNN**
* 🧠 Face recognition using **dlib / face_recognition**
* ✅ Automatic attendance marking
* 🕐 Automatic `IN` / `OUT` attendance tracking
* 📊 Attendance dashboard and statistics
* 👥 Register and remove known persons
* 🚨 Detect and store unknown faces
* 🔄 Register an unknown face as a known person
* 📋 View attendance logs
* 📥 Export attendance as an Excel file
* 🔌 REST API using FastAPI
* ⚡ Real-time camera updates using WebSocket
* 📱 Responsive React dashboard
* 🌑 Industrial-style dark UI

The React application provides separate pages for Dashboard, Live Camera, Persons, Attendance Logs, and Unknown Faces.

---

## System Architecture

```text
                    ┌──────────────────────┐
                    │     CCTV / Webcam    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        OpenCV        │
                    │   Camera Capture     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        MTCNN         │
                    │    Face Detection    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  face_recognition    │
                    │  dlib Face Encoding  │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
          Known Person                 Unknown Person
                  │                         │
                  ▼                         ▼
        Attendance Record           Save Face Image
                  │                         │
                  └────────────┬────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │      REST + WS       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     React Frontend   │
                    │     Web Dashboard    │
                    └──────────────────────┘
```

---

## Technology Stack

### Backend

* Python
* FastAPI
* OpenCV
* MTCNN
* `face_recognition`
* dlib
* NumPy
* Pandas
* openpyxl
* WebSockets

The backend initializes MTCNN and loads known face encodings when the FastAPI application starts.

### Frontend

* React
* React Router
* Axios
* CSS
* WebSocket API

The frontend communicates with the backend through Axios and maintains a WebSocket connection for live camera data.

### Storage

The application uses:

```text
known_faces/
attendance.xlsx
unknown_faces/
```

The backend creates the face directories automatically if they do not already exist.

---

# Project Structure

A recommended project structure is:

```text
CCTV_FACE_ATTENDANCE/
│
├── backend/
│   ├── main.py
│   ├── known_faces/
│   ├── unknown_faces/
│   └── attendance.xlsx
│
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── api.js
│   │   └── pages/
│   │       ├── Dashboard.js
│   │       ├── LiveCamera.js
│   │       ├── Persons.js
│   │       ├── AttendanceLogs.js
│   │       └── UnknownFaces.js
│   │
│   └── package.json
│
├── CCTV_FACE_ATTENDANCE.py
└── README.md
```

> The exact frontend `pages/` implementations and `package.json` were not included in the uploaded files, so the structure above reflects the routes referenced by `App.js` rather than inventing their contents.

---

# Backend Setup

## 1. Install Python

Use Python 3.9+ if possible.

Create and activate a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Install Dependencies

Install the required packages:

```bash
pip install fastapi uvicorn opencv-python face-recognition pandas openpyxl mtcnn numpy python-multipart
```

Depending on the operating system, installing `dlib` / `face-recognition` may require additional build tools.

---

## 3. Start the Backend

From the backend directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI's health endpoint is:

```text
GET /api/health
```

and returns:

```json
{
  "status": "ok"
}
```

The frontend defaults to `http://localhost:8000` when `REACT_APP_API_URL` is not specified.

---

# Frontend Setup

Install the frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm start
```

The React application contains these main routes:

| Route      | Purpose            |
| ---------- | ------------------ |
| `/`        | Dashboard          |
| `/camera`  | Live Camera        |
| `/persons` | Registered Persons |
| `/logs`    | Attendance Logs    |
| `/unknown` | Unknown Faces      |

These routes are defined in `App.js`.

---

# Environment Configuration

The frontend API URL can be configured with:

```env
REACT_APP_API_URL=http://localhost:8000
```

If this variable is not provided, the frontend uses:

```text
http://localhost:8000
```

as its API server.

---

# Registering People

Known faces are stored in:

```text
known_faces/
```

The backend recognizes `.jpg`, `.jpeg`, and `.png` files in this directory and uses the filename (without the extension) as the person's name.

For example:

```text
known_faces/
├── Alice.jpg
├── Bob.jpg
└── Charlie.jpg
```

will create registered identities:

```text
Alice
Bob
Charlie
```

You can also register a person through the API:

```http
POST /api/persons/register
```

with:

* `name`
* `file`

After registration, the backend reloads the known face encodings.

---

# Face Detection & Recognition

The system uses two stages.

### 1. MTCNN Detection

MTCNN detects faces and provides:

* Bounding box
* Detection confidence
* Facial keypoints

Only detections with confidence of at least:

```text
0.90
```

are processed.

### 2. Face Recognition

The detected face is passed to `face_recognition`, which generates a face encoding.

The encoding is compared with the registered face encodings using:

```text
tolerance = 0.6
```

The closest matching registered face is used when the match passes the configured tolerance.

---

# Attendance Logic

Attendance is stored in:

```text
attendance.xlsx
```

Each record contains:

| Field    | Description              |
| -------- | ------------------------ |
| `Name`   | Recognized person's name |
| `Date`   | Attendance date          |
| `Time`   | Attendance time          |
| `Status` | `IN` or `OUT`            |

The backend creates an `IN` record when a registered person is detected for the first time on a given day.

An `OUT` record is created when the same person's detection occurs at least **7 hours** after their recorded `IN` time.

The configured value is:

```python
OUT_TIME_GAP_HOURS = 7
```

---

# Unknown Face Detection

When a detected face cannot be matched to a registered person, it is classified as:

```text
Unknown
```

Unknown face images are stored in:

```text
unknown_faces/
```

with timestamp-based filenames such as:

```text
unknown_20260923_104500.jpg
```

The backend exposes an endpoint for retrieving these images:

```http
GET /api/unknown-faces
```

Images are returned as Base64-encoded JPEG data.

Unknown faces can also be:

* Deleted individually
* Cleared in bulk
* Registered as a known person

---

# REST API

## Health

### Check server health

```http
GET /api/health
```

---

## Camera

### Start camera

```http
POST /api/camera/start
```

### Stop camera

```http
POST /api/camera/stop
```

### Camera status

```http
GET /api/camera/status
```

The camera uses OpenCV and is configured for:

```text
640 × 480
30 FPS
```

The API implementation exposes these camera controls directly.

---

## Persons

### Get registered persons

```http
GET /api/persons
```

### Register person

```http
POST /api/persons/register
```

Form fields:

```text
name
file
```

### Delete person

```http
DELETE /api/persons/{id}
```

The corresponding frontend API functions are implemented in `api.js`.

---

## Attendance

### Get all attendance

```http
GET /api/attendance
```

### Get today's attendance

```http
GET /api/attendance/today
```

### Get statistics

```http
GET /api/attendance/stats
```

### Export attendance

```http
GET /api/attendance/export
```

The export endpoint returns the attendance Excel file.

---

## Unknown Faces

### Get unknown faces

```http
GET /api/unknown-faces
```

### Delete one unknown face

```http
DELETE /api/unknown-faces/{id}
```

### Delete all unknown faces

```http
DELETE /api/unknown-faces
```

### Register unknown face

```http
POST /api/unknown-faces/register/{id}
```

Request:

```json
{
  "name": "Person Name"
}
```

---

# WebSocket Camera Stream

The live camera uses:

```text
/ws/camera
```

The frontend creates a WebSocket connection using:

```text
/ws/camera
```

and receives JSON messages containing:

```json
{
  "type": "frame",
  "image": "...",
  "boxes": [],
  "width": 640,
  "height": 480
}
```

Each detected face can contain:

```json
{
  "left": 100,
  "top": 80,
  "width": 120,
  "height": 120,
  "name": "Alice",
  "confidence": 0.98
}
```

The backend encodes camera frames as JPEG and sends them through the WebSocket connection.

---

# Frontend API Client

The frontend uses Axios for communication with the backend.

The API client provides functions for:

```text
checkHealth()
startCamera()
stopCamera()
getCameraStatus()

getPersons()
registerPerson()
deletePerson()

getAttendance()
getTodayAttendance()
getStats()
exportAttendance()

getUnknownFaces()
createWebSocket()
```

---

# Dashboard

The dashboard is designed around an industrial dark theme with:

* System statistics
* Camera monitoring
* Attendance information
* Registered people
* Unknown face alerts
* Event/activity information
* Tables and filters

The UI uses a dark color palette with accent, danger, warning, and information states.

The interface is also responsive; at smaller screen widths the sidebar collapses and multi-column layouts become single-column layouts.

---

# Standalone CCTV Application

The project also contains:

```text
CCTV_FACE_ATTENDANCE.py
```

This provides a standalone OpenCV-based version of the attendance system without the web dashboard.

It:

1. Initializes MTCNN.
2. Loads known faces.
3. Opens the webcam.
4. Detects faces.
5. Recognizes registered people.
6. Marks attendance.
7. Saves unknown faces.
8. Displays a live OpenCV dashboard.

The standalone application processes MTCNN detections every two frames for performance optimization.

Run it with:

```bash
python CCTV_FACE_ATTENDANCE.py
```

Press:

```text
Q
```

or:

```text
ESC
```

to exit.

---

# Performance

The system intentionally does not run face detection on every camera frame.

The web backend processes detection every **5th frame**:

```python
detection_interval = 5
```

while the standalone application processes every **2nd frame**.
This reduces the computational workload while maintaining a responsive live feed.

---

# Data Files

## `attendance.xlsx`

Stores attendance information:

```text
Name | Date | Time | Status
```

Example:

```text
Alice | 2026-09-23 | 09:02:15 | IN
Alice | 2026-09-23 | 17:10:21 | OUT
```

## `known_faces/`

Contains registered face images.

```text
known_faces/
├── Alice.jpg
├── Bob.jpg
└── Charlie.jpg
```

## `unknown_faces/`

Contains faces that could not be matched to registered people.

```text
unknown_faces/
├── unknown_20260923_090120.jpg
└── unknown_20260923_091530.jpg
```

---

# Configuration

The main recognition parameters are:

```python
OUT_TIME_GAP_HOURS = 7
MTCNN_CONFIDENCE_THRESHOLD = 0.9
```

The backend stores application data relative to the backend's directory, while the standalone `CCTV_FACE_ATTENDANCE.py` currently contains Windows-specific absolute paths.
For portability, prefer the backend's relative-directory approach when deploying the application on another machine.

---

# Troubleshooting

## Camera does not start

Check that:

* A webcam/CCTV camera is connected.
* The camera is not being used by another application.
* OpenCV can access the camera.
* The backend has permission to access the camera.

The backend uses:

```python
cv2.VideoCapture(0)
```

for the default camera.

---

## No faces are recognized

Check that:

1. The person has been registered.
2. Their image contains a clearly detectable face.
3. The image is stored in `known_faces/`.
4. Lighting and camera quality are adequate.
5. The face-recognition dependencies are installed correctly.

---

## No attendance file exists

This is expected on a fresh installation.

## The application creates `attendance.xlsx` when the first attendance record is written, and the export endpoint can also initialize an empty workbook.

## Frontend cannot connect to backend

Check that the backend is running:

```bash
uvicorn main:app --reload --port 8000
```

Then verify:

```text
GET http://localhost:8000/api/health
```

Also verify:

```env
REACT_APP_API_URL=http://localhost:8000
```

---

# Security Considerations

This project is intended as an attendance/monitoring application and should be deployed with appropriate security controls.

Before production deployment, consider:

* Authentication and authorization
* HTTPS/WSS
* Restricted CORS origins
* Secure storage of face data
* Access controls for attendance records
* Protection of exported Excel files
* Retention/deletion policies for unknown faces
* Camera access permissions
* Audit logging

The current FastAPI configuration allows all CORS origins:

```python
allow_origins=["*"]
```

so this should be restricted for a production deployment.

---

# Privacy

This application processes biometric face data and attendance information.

Before deploying it in a real organization, ensure that its use complies with applicable privacy, employment, biometric-data, and data-protection requirements.

In particular, establish:

* Who can register people
* Who can view attendance
* How long face images are retained
* How unknown-face images are handled
* Who can export attendance data
* How users can request correction or deletion where applicable

---

# Development Notes

The application consists of two complementary components:

```text
Standalone Python Application
        │
        └── CCTV_FACE_ATTENDANCE.py

Web Application
        │
        ├── FastAPI Backend
        │      └── main.py
        │
        └── React Frontend
               ├── App.js
               ├── App.css
               └── api.js
```

The React application identifies itself as:

```text
CCTV Watch
Attendance System
v2.0.0 · MTCNN + dlib
```

---

# Future Improvements

Potential improvements include:

* Multiple CCTV camera support
* RTSP/IP camera support
* User authentication
* Role-based access control
* PostgreSQL/MySQL database support
* Better attendance-session management
* Configurable `IN`/`OUT` rules
* Face-recognition confidence configuration from the UI
* Automatic report generation
* Email/notification alerts
* HTTPS and secure WebSockets
* Docker deployment
* Cloud deployment
* Improved face-recognition performance
* Attendance correction and approval workflow

---

# License

No license information was included in the provided project files.

Add an appropriate license before publishing or distributing the project.

---

## Summary

**CCTV Face Attendance System** combines computer vision, face recognition, FastAPI, WebSockets, React, and Excel-based storage to provide a real-time attendance monitoring application.

Core technologies:

```text
MTCNN
   ↓
Face Detection
   ↓
face_recognition / dlib
   ↓
Face Matching
   ↓
Attendance / Unknown Face
   ↓
FastAPI
   ↓
React Dashboard
```

The project is designed around real-time CCTV monitoring while providing management interfaces for registered persons, attendance records, and unknown-face detections.
