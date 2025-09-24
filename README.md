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



**Building the Executable (Windows)**
If you want to run SitSmartCoach without installing Python or dependencies, you can build a standalone executable using PyInstaller:

Step 1: Install PyInstaller

Activate your Python virtual environment and install PyInstaller:

Activate virtual environment (Windows PowerShell)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

Install PyInstaller
pip install pyinstaller

Step 2: Build the Executable

Run PyInstaller with the following command from the project root directory:

pyinstaller --onefile --noconsole --hidden-import=cv2 --hidden-import=mediapipe --hidden-import=numpy SitSmartCoach.py


**Building the Executable (Windows)**
--onefile → Packages everything into a single .exe file

--noconsole → Hides the console window for a clean GUI experience

--hidden-import → Ensures PyInstaller includes dependencies that may not be auto-detected

After building, the executable will be located in the dist folder:

SitSmartCoach\dist\SitSmartCoach.exe

Step 3: Run the Executable

Navigate to the dist folder in File Explorer.

Double-click SitSmartCoach.exe to launch the application.

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

