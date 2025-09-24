import os
import sys
import cv2
import time
import queue
import ctypes
import getpass
import threading
import numpy as np
import tkinter as tk
import traceback
import datetime as dt

# -------- Logging --------
LOG_PATH = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "SitSmartCoach.log")
def log(msg: str):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass
log("=== SitSmartCoach starting ===")

# -------- Import mediapipe --------
try:
    import mediapipe as mp
    log(f"mediapipe imported from: {os.path.dirname(mp.__file__)}")
except Exception as e:
    log("ERROR importing mediapipe:\n" + traceback.format_exc())
    raise
mp_pose = mp.solutions.pose

# -------- Config --------
ELBOW_MIN, ELBOW_MAX = 50, 180
DIST_MIN_CM, DIST_MAX_CM = 70, 100
AVG_SHOULDER_WIDTH_CM = 30
FOCAL_LENGTH_PX = 650
SMOOTH_N = 7
UI_REFRESH_MS = 400
WORKER_SLEEP_S = 0.05

# -------- Helper Functions --------
def calculate_angle(a, b, c) -> float:
    a, b, c = np.array(a), np.array(b), np.array(c)
    ang = np.degrees(np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0]))
    ang = abs(ang)
    return 360.0 - ang if ang > 180 else ang

def estimate_distance_cm(left_sh_px, right_sh_px) -> float:
    try:
        dpx = float(np.linalg.norm(np.array(left_sh_px) - np.array(right_sh_px)))
        if dpx <= 1e-6: return 0.0
        z = (FOCAL_LENGTH_PX * AVG_SHOULDER_WIDTH_CM) / dpx
        return float(z)
    except Exception:
        return 0.0

def center_gaze_label(nose_x, left_sh_x, right_sh_x) -> str:
    cx = (left_sh_x + right_sh_x) / 2.0
    diff = nose_x - cx
    if diff < -0.03: return "👀 Looking Left"
    elif diff > 0.03: return "👀 Looking Right"
    else: return "👀 Looking Center"

# -------- Startup Functions --------
def _startup_paths():
    user = getpass.getuser()
    startup_dir = os.path.join("C:\\Users", user, "AppData", "Roaming", "Microsoft", "Windows",
                               "Start Menu", "Programs", "Startup")
    exe_name = "SitSmartCoach.exe"
    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.join(os.getcwd(), exe_name)
    lnk_path = os.path.join(startup_dir, "SitSmartCoach.lnk")
    return startup_dir, exe_path, lnk_path

def add_to_startup():
    try:
        startup_dir, exe_path, lnk_path = _startup_paths()
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        log("Added to startup.")
    except Exception as e:
        log("Failed to add to startup: " + str(e))

def remove_from_startup():
    try:
        _, _, lnk_path = _startup_paths()
        if os.path.exists(lnk_path):
            os.remove(lnk_path)
        log("Removed from startup.")
    except Exception as e:
        log("Failed to remove from startup: " + str(e))

# -------- Camera Worker --------
class PostureWorker(threading.Thread):
    def __init__(self, out_queue: queue.Queue):
        super().__init__(daemon=True)
        self.q = out_queue
        self._stop_evt = threading.Event()
        self._pose = None
        self._cam = None
        self.angles, self.dists, self.gazes = [], [], []
        self.paused = False
        self.initialized = False
        self.move_msg_shown = False

    def stop(self):
        self._stop_evt.set()

    def run(self):
        try:
            self._cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self._cam.isOpened():
                self.q.put(["⚠️ Camera not detected"])
                log("Camera open failed.")
                return

            self._pose = mp_pose.Pose(min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5,
                                      model_complexity=1)
            log("Pose model created.")

            while not self._stop_evt.is_set():
                if self.paused:
                    time.sleep(0.1)
                    continue

                ok, frame = self._cam.read()
                if not ok:
                    self.q.put(["⚠️ Unable to read from camera"])
                    time.sleep(0.1)
                    continue

                ih, iw = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = self._pose.process(rgb)
                msgs = []

                try:
                    if res.pose_landmarks is None:
                        msgs = ["⚠️ Move into Frame"]
                        self.move_msg_shown = True
                    else:
                        lm = res.pose_landmarks.landmark
                        nose = lm[mp_pose.PoseLandmark.NOSE.value]
                        lsh = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                        rsh = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

                        if any([nose.visibility < 0.5, lsh.visibility < 0.5, rsh.visibility < 0.5]):
                            msgs = ["⚠️ Move into Frame"]
                            self.move_msg_shown = True
                        else:
                            self.move_msg_shown = False
                            # Elbow
                            lel = lm[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                            lwr = lm[mp_pose.PoseLandmark.LEFT_WRIST.value]
                            ang = calculate_angle((lsh.x, lsh.y), (lel.x, lel.y), (lwr.x, lwr.y))
                            self.angles.append(ang)
                            if len(self.angles) > SMOOTH_N: self.angles.pop(0)
                            ang_sm = float(np.median(self.angles))
                            msgs.append("🏋️‍♂️ " + ("Elbow OK" if ELBOW_MIN <= ang_sm <= ELBOW_MAX else "Adjust Elbow"))

                            # Distance
                            lsh_px = (lsh.x * iw, lsh.y * ih)
                            rsh_px = (rsh.x * iw, rsh.y * ih)
                            z_cm = estimate_distance_cm(lsh_px, rsh_px)
                            if z_cm > 0:
                                self.dists.append(z_cm)
                                if len(self.dists) > SMOOTH_N: self.dists.pop(0)
                                z_sm = float(np.median(self.dists))
                                if DIST_MIN_CM <= z_sm <= DIST_MAX_CM:
                                    msgs.append("📏 Distance OK")
                                elif z_sm < DIST_MIN_CM:
                                    msgs.append("📏 Too Close")
                                else:
                                    msgs.append("📏 Too Far")
                            else:
                                msgs.append("⚠️ Move into Frame")

                            # Gaze
                            nose_x = nose.x
                            gaze = center_gaze_label(nose_x, lsh.x, rsh.x)
                            self.gazes.append(gaze)
                            if len(self.gazes) > SMOOTH_N: self.gazes.pop(0)
                            gaze_final = max(set(self.gazes), key=self.gazes.count)
                            msgs.append(gaze_final)
                            self.initialized = True
                except Exception:
                    msgs = ["⚠️ Move into Frame"]
                    self.move_msg_shown = True

                # Push messages to queue
                if msgs:
                    try:
                        while not self.q.empty(): self.q.get_nowait()
                        self.q.put_nowait(msgs)
                    except queue.Full:
                        pass
                time.sleep(WORKER_SLEEP_S)

        except Exception:
            log("Worker crashed:\n" + traceback.format_exc())
            try: self.q.put(["⚠️ Internal Error – see log"])
            except Exception: pass
        finally:
            if self._pose: self._pose.close()
            if self._cam and self._cam.isOpened(): self._cam.release()
            log("Worker stopped.")

# -------- GUI --------
class FloatingPopup(tk.Tk):
    def __init__(self, q: queue.Queue, worker: PostureWorker):
        super().__init__()
        self.q = q
        self.worker = worker
        self.in_rest = False
        self.rest_btn = None
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#f0f0f0")
        self.geometry("+200+200")

        # Panel
        self.panel = tk.Frame(self, bg="#ffffff", bd=2, relief="raised")
        self.panel.pack(padx=5, pady=5)

        # Messages
        self.msg_labels = []
        lbl_init = tk.Label(self.panel, text="Initializing...", font=("Segoe UI", 12),
                            bg="#ffffff", fg="#333333", anchor="w")
        lbl_init.pack(fill="x", padx=8, pady=4)
        self.msg_labels.append(lbl_init)
        for _ in range(3):
            lbl = tk.Label(self.panel, text="", font=("Segoe UI", 12),
                           bg="#ffffff", fg="#333333", anchor="w")
            lbl.pack(fill="x", padx=8, pady=4)
            self.msg_labels.append(lbl)

        # Controls
        ctrl_frame = tk.Frame(self.panel, bg="#ffffff")
        ctrl_frame.pack(pady=5)
        tk.Button(ctrl_frame, text="❌ Exit", command=self.quit_app,
                  bg="#CC3333", fg="white", bd=0, padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(ctrl_frame, text="🟢 Add Startup", command=add_to_startup,
                  bg="#2E7D32", fg="white", bd=0, padx=10, pady=4).pack(side="left", padx=4)
        tk.Button(ctrl_frame, text="⚪ Remove Startup", command=remove_from_startup,
                  bg="#CCCCCC", fg="#111111", bd=0, padx=10, pady=4).pack(side="left", padx=4)

        # Reminder interval
        interval_frame = tk.Frame(self.panel, bg="#ffffff")
        interval_frame.pack(pady=5)
        tk.Label(interval_frame, text="Reminder Interval:", font=("Segoe UI", 10), bg="#ffffff").pack(side="left", padx=4)
        self.interval_var = tk.IntVar(value=1)
        interval_menu = tk.OptionMenu(interval_frame, self.interval_var, 30, 45, 60, 120, command=self._update_interval)
        interval_menu.config(bg="#dddddd", fg="#000000", bd=0, highlightthickness=0)
        interval_menu.pack(side="left", padx=4)
        self.rest_interval_ms = self.interval_var.get() * 60_000

        # Dragging
        self.bind("<Button-1>", self._start_move)
        self.bind("<B1-Motion>", self._do_move)
        try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception: pass

        # Start periodic updates
        self.after(UI_REFRESH_MS, self._pump_queue)
        self.after(self.rest_interval_ms, self._rest_reminder)

    # Drag
    def _start_move(self, e): self._mx, self._my = e.x, e.y
    def _do_move(self, e): self.geometry(f"+{e.x_root - getattr(self, '_mx', 0)}+{e.y_root - getattr(self, '_my', 0)}")

    # Update messages
    def _pump_queue(self):
        if not self.in_rest:
            try:
                msgs = None
                try:
                    while True: msgs = self.q.get_nowait()
                except queue.Empty: pass

                if msgs:
                    for lbl, msg in zip(self.msg_labels, msgs):
                        color = "#c8e6c9" if "OK" in msg else "#fff9c4" if "⚠️" in msg else "#bbdefb"
                        lbl.config(text=msg, bg=color)
            finally:
                self.after(UI_REFRESH_MS, self._pump_queue)
        else:
            self.after(UI_REFRESH_MS, self._pump_queue)

    # Rest reminder
    def _rest_reminder(self):
        self.in_rest = True
        self.worker.paused = True
        # Hide all regular feedback
        for lbl in self.msg_labels:
            lbl.pack_forget()
        # Show only attractive rest message
        self.rest_label = tk.Label(self.panel, text="⏰ Take a Break!\nStretch & Relax 🧘‍♂️", 
                                   font=("Segoe UI", 16, "bold"), bg="#FFECB3", fg="#BF360C",
                                   relief="raised", bd=2, padx=20, pady=20, justify="center")
        self.rest_label.pack(pady=20)
        if not self.rest_btn:
            self.rest_btn = tk.Button(self.panel, text="✅ OK", command=self._end_rest,
                                      bg="#1976D2", fg="white", bd=0, padx=12, pady=6, font=("Segoe UI", 12, "bold"))
            self.rest_btn.pack(pady=10)

    def _end_rest(self):
        self.in_rest = False
        self.worker.paused = False
        if self.rest_label: self.rest_label.destroy(); self.rest_label = None
        if self.rest_btn: self.rest_btn.destroy(); self.rest_btn = None
        for lbl in self.msg_labels:
            lbl.pack(fill="x", padx=8, pady=4)
            lbl.config(text="✅ Resumed. Stay Healthy!", bg="#c8e6c9")
        self.after(self.rest_interval_ms, self._rest_reminder)

    def _update_interval(self, *args):
        self.rest_interval_ms = self.interval_var.get() * 60_000
        log(f"Rest interval updated to {self.interval_var.get()} minutes.")

    def quit_app(self): self.destroy()

# -------- Main --------
def main():
    q = queue.Queue(maxsize=2)
    worker = PostureWorker(q)
    worker.start()
    app = FloatingPopup(q, worker)
    try:
        app.mainloop()
    finally:
        worker.stop()
        worker.join(timeout=1.5)
        log("UI closed. Goodbye.")

if __name__ == "__main__":
    main()