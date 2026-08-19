import cv2
import math
import time
import os
import datetime
import threading
from motion_detection import MotionDetector
import config
import event_logger

class CameraHandler:
    def __init__(self):
        self.camera_index = config.CAMERA_INDEX
        self.cap = None
        self.running = False
        self.thread = None
        self.latest_frame = None
        self.latest_processed_frame = None
        self.detector = MotionDetector()
        self.lock = threading.Lock()
        
        # Callback when abnormal motion is detected
        self.abnormal_motion_callback = None
        
        # Track latest saved image name for dashboard reference
        self.latest_captured_image_name = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, name="CameraThread", daemon=True)
        self.thread.start()
        print("[CAMERA] Camera processing thread started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.release_camera()
        print("[CAMERA] Camera thread stopped.")

    def init_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            if not self.cap.isOpened():
                print(f"[CAMERA WARNING] Could not open webcam index {self.camera_index}. Operating in SIMULATION mode.")
                self.cap = None
        except Exception as e:
            print(f"[CAMERA ERROR] Exception initializing camera: {e}")
            self.cap = None

    def release_camera(self):
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None

    def _capture_loop(self):
        self.init_camera()
        
        # Variables for simulation fallback
        sim_angle = 0
        
        while self.running:
            frame = None
            
            # 1. Attempt to read a real frame
            if self.cap is not None:
                ret, raw_frame = self.cap.read()
                if ret:
                    frame = raw_frame
                else:
                    print("[CAMERA] Failed to read frame from webcam. Retrying camera reset...")
                    self.release_camera()
                    time.sleep(1.0)
                    self.init_camera()
            
            # 2. Simulation fallback: Generate a simulated camera feed if camera not present
            if frame is None:
                import numpy as np
                frame = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
                
                # Draw dark textured grid background
                for x in range(0, config.FRAME_WIDTH, 40):
                    cv2.line(frame, (x, 0), (x, config.FRAME_HEIGHT), (20, 20, 25), 1)
                for y in range(0, config.FRAME_HEIGHT, 40):
                    cv2.line(frame, (0, y), (config.FRAME_WIDTH, y), (20, 20, 25), 1)
                
                # Draw dynamic moving target (to simulate motion)
                sim_angle += 0.05
                target_x = int(config.FRAME_WIDTH / 2 + math.cos(sim_angle) * 150)
                target_y = int(config.FRAME_HEIGHT / 2 + math.sin(sim_angle * 2) * 100)
                
                # Periodically simulate a fast "abnormal" burst of motion
                current_sec = time.time() % 30
                if 12.0 < current_sec < 14.0:
                    # High speed erratic movement
                    target_x += int(math.sin(sim_angle * 10) * 100)
                    target_y += int(math.cos(sim_angle * 15) * 80)
                    cv2.circle(frame, (target_x, target_y), 35, (100, 100, 250), -1)
                else:
                    # Normal smooth movement
                    cv2.circle(frame, (target_x, target_y), 20, (0, 200, 0), -1)
                
                # Overlay system label
                cv2.putText(frame, "[CAMERA SIMULATION ACTIVE]", (20, config.FRAME_HEIGHT - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
            
            # Save raw frame
            with self.lock:
                self.latest_frame = frame.copy()
            
            # 3. Feed frame into CV Motion Detector
            processed, abnormal, alert_type = self.detector.process_frame(frame)
            
            with self.lock:
                self.latest_processed_frame = processed
            
            # 4. Trigger callback if abnormal motion is detected
            if abnormal:
                event_logger.log_motion(f"Abnormal motion alert triggered: {alert_type}")
                # Save snapshot automatically
                self.capture_snapshot(alert_type.replace(" ", "_"))
                
                if self.abnormal_motion_callback:
                    # Run callback in non-blocking thread
                    threading.Thread(target=self.abnormal_motion_callback, args=(alert_type,), daemon=True).start()
            
            # Control frame rate (approx 20-30 FPS)
            time.sleep(0.04)

    def get_latest_jpeg(self):
        with self.lock:
            frame_to_encode = self.latest_processed_frame
            
        if frame_to_encode is None:
            # Generate a blank fallback frame
            import numpy as np
            frame_to_encode = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame_to_encode, "CAMERA LOADING...", (150, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
        ret, jpeg = cv2.imencode('.jpg', frame_to_encode)
        if ret:
            return jpeg.tobytes()
        return None

    def capture_snapshot(self, reason):
        """
        Captures the current raw frame and saves it as an image file.
        """
        with self.lock:
            frame_to_save = self.latest_frame
            
        if frame_to_save is None:
            print("[CAMERA] Cannot capture snapshot; frame is empty.")
            return None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}_{reason}.jpg"
        filepath = os.path.join(config.CAPTURED_IMAGES_DIR, filename)
        
        try:
            # Annotate with a timestamp before saving
            annotated = frame_to_save.copy()
            ts_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated, f"CAPTURE TIME: {ts_str}", (15, config.FRAME_HEIGHT - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(annotated, f"TRIGGER: {reason}", (15, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            cv2.imwrite(filepath, annotated)
            print(f"[CAMERA] Snapshot captured and saved: {filepath}")
            
            with self.lock:
                self.latest_captured_image_name = filename
                
            return filename
        except Exception as e:
            print(f"[CAMERA ERROR] Failed to save snapshot: {e}")
            return None
            
    def get_latest_captured_image(self):
        with self.lock:
            return self.latest_captured_image_name
