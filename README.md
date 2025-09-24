# Sit-Smart-Coach-Posture-detection
SitSmartCoach is a lightweight, real-time posture monitoring and reminder application designed to help users maintain healthy sitting habits. Using computer vision powered by MediaPipe and OpenCV, it tracks shoulder and elbow positions, estimates distance from the screen, and provides gaze direction feedback to ensure proper ergonomics during work or study sessions.

**Features**

 Real-time posture detection using your webcam

 Distance monitoring to maintain optimal workspace ergonomics

 Elbow angle guidance for healthy sitting posture

 Gaze tracking to prevent slouching or leaning

 Periodic reminders for breaks, stretches, and eye relaxation

 Floating popup GUI that runs on top of other applications

 Optional startup integration for automatic launch on Windows

**Installation**
Using Python

Clone the repository:

git clone https://github.com/<your-username>/SitSmartCoach.git
cd SitSmartCoach


Create and activate a virtual environment (Windows example):

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1


Install dependencies:

pip install -r requirements.txt


Run the application:

python SitSmartCoach.py

Standalone Executable

A pre-built Windows executable is available in the dist folder:

Double-click SitSmartCoach.exe to launch the app without installing Python or dependencies.

Usage

On launch, a floating popup provides real-time posture feedback.

Messages:

🏋️‍♂️ Elbow OK / Adjust Elbow

📏 Distance OK / Too Close / Too Far

👀 Looking Left / Right / Center

Break reminders: Configurable interval from 30 to 120 minutes.

Add or remove from startup using the buttons in the popup.

**Dependencies**

Python 3.11

OpenCV (opencv-python)

MediaPipe (mediapipe)

NumPy (numpy)

PyWin32 (pywin32)

(See requirements.txt for full version details)

**Development**

The project uses threading for real-time camera processing.

The GUI is built with Tkinter and runs independently of the camera worker thread.

Logging is implemented to track errors and application events in SitSmartCoach.log.

**License**

This project is licensed under the MIT License – see LICENSE
 for details.

**Contributing**

Contributions are welcome! Please fork the repository and submit pull requests with clear descriptions of your changes.

