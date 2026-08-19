import cv2
import numpy as np
import time
import math
from collections import deque
import config

class MotionDetector:
    def __init__(self):
        # Background subtraction using MOG2
        self.back_sub = cv2.createBackgroundSubtractorMOG2(
            history=config.BG_HISTORY, 
            varThreshold=config.BG_VAR_THRESHOLD, 
            detectShadows=True
        )
        
        # Keep track of the previous gray frame for frame differencing (speed calculation)
        self.prev_gray = None
        
        # Centroid history to compute velocity/speed
        self.prev_centroid = None
        
        # Sliding history buffers (deque) for running averages
        self.intensity_history = deque(maxlen=30)
        self.speed_history = deque(maxlen=30)
        
        # Peak motion timestamps for frequency analysis
        self.motion_peaks = deque()
        self.last_peak_time = 0
        self.in_motion = False
        
        # Alert cooldown to prevent rapid repeated alerts
        self.last_alert_time = 0
        
    def process_frame(self, frame):
        """
        Process a single BGR frame.
        Returns:
            annotated_frame (numpy.ndarray): Frame with drawings and telemetry
            abnormal_detected (bool): True if any abnormal motion threshold exceeded
            alert_type (str): Specific trigger description, or empty string
        """
        height, width = frame.shape[:2]
        total_pixels = height * width
        
        # Convert to grayscale and blur to reduce noise
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # 1. Background subtraction mask
        fg_mask = self.back_sub.apply(frame)
        
        # Clean up shadow values (MOG2 shadows are labeled 127) and threshold noise
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # 2. Frame differencing for local frame-to-frame change (speed tracking)
        delta_speed = 0.0
        current_centroid = None
        
        if self.prev_gray is not None:
            frame_diff = cv2.absdiff(self.prev_gray, gray_blurred)
            _, diff_thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            diff_thresh = cv2.dilate(diff_thresh, None, iterations=2)
            
            # Find contours in frame difference (actual moving boundaries)
            diff_contours, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            largest_contour = None
            max_area = 0
            for c in diff_contours:
                area = cv2.contourArea(c)
                if area > config.MIN_MOTION_AREA and area > max_area:
                    max_area = area
                    largest_contour = c
                    
            if largest_contour is not None:
                # Calculate centroid of the moving boundary
                M = cv2.moments(largest_contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    current_centroid = (cx, cy)
                    
                    # If we had a previous centroid, calculate displacement (speed)
                    if self.prev_centroid is not None:
                        dx = current_centroid[0] - self.prev_centroid[0]
                        dy = current_centroid[1] - self.prev_centroid[1]
                        delta_speed = math.sqrt(dx*dx + dy*dy)
        
        # Store gray frame for next iteration
        self.prev_gray = gray_blurred
        
        # 3. Motion Intensity Analysis
        # Count white pixels in fg_mask (areas undergoing change compared to background)
        moving_pixels = cv2.countNonZero(fg_mask)
        intensity = (moving_pixels / total_pixels) * 100.0  # Percentage of screen
        
        # 4. Filter and smooth signals
        self.intensity_history.append(intensity)
        self.speed_history.append(delta_speed)
        
        avg_intensity = sum(self.intensity_history) / len(self.intensity_history) if self.intensity_history else 0
        avg_speed = sum(self.speed_history) / len(self.speed_history) if self.speed_history else 0
        
        # Find contours of moving foreground clusters for visualization
        fg_contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw bounding boxes around foreground motion
        motion_detected = False
        for c in fg_contours:
            if cv2.contourArea(c) > config.MIN_MOTION_AREA:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
        if current_centroid is not None:
            cv2.circle(frame, current_centroid, 8, (0, 0, 255), -1)
            self.prev_centroid = current_centroid
        
        # 5. Motion Frequency Analysis
        current_time = time.time()
        # Clean up peak timestamps older than the sliding window
        while self.motion_peaks and (current_time - self.motion_peaks[0] > config.MOTION_FREQUENCY_WINDOW_SEC):
            self.motion_peaks.popleft()
            
        # Detect a "motion peak" (rapid change/transition from quiet to active, or speed surge)
        if motion_detected and not self.in_motion:
            self.in_motion = True
            if current_time - self.last_peak_time > 0.5:  # Debounce peaks by 500ms
                self.motion_peaks.append(current_time)
                self.last_peak_time = current_time
        elif not motion_detected:
            self.in_motion = False
            
        frequency = len(self.motion_peaks)
        
        # 6. Abnormal Motion Decision Logic
        abnormal_detected = False
        alert_type = ""
        
        # Sudden Fast Movement (instantaneous speed exceeds threshold)
        if delta_speed > config.MOTION_SPEED_THRESHOLD:
            abnormal_detected = True
            alert_type = "SUDDEN FAST MOVEMENT"
            
        # Excessive Motion (intensity percentage exceeds threshold)
        elif intensity > config.MOTION_INTENSITY_THRESHOLD:
            abnormal_detected = True
            alert_type = "EXCESSIVE MOTION"
            
        # Suspicious Repeated Movement (frequency exceeds threshold)
        elif frequency >= config.MOTION_FREQUENCY_THRESHOLD:
            abnormal_detected = True
            alert_type = "SUSPICIOUS REPEATED MOTION"
            
        # Abnormal Pattern: Spike relative to rolling history
        # (Only evaluate if there is actual motion to avoid dividing by/comparing with zero noise)
        elif delta_speed > 10.0 and len(self.speed_history) >= 15:
            historical_avg_speed = sum(list(self.speed_history)[:-1]) / (len(self.speed_history) - 1)
            if historical_avg_speed > 2.0 and (delta_speed > historical_avg_speed * 4.0):
                abnormal_detected = True
                alert_type = "ABNORMAL VELOCITY SPIKE"
                
        # Cooldown management for reporting
        is_cooldown_expired = (current_time - self.last_alert_time) > config.ABNORMAL_MOTION_COOLDOWN
        if abnormal_detected and is_cooldown_expired:
            self.last_alert_time = current_time
        else:
            # If still within cooldown or not abnormal, return false to prevent spamming
            abnormal_detected = False
            if not is_cooldown_expired and alert_type != "":
                # Keep showing label on feed but don't fire new system alerts
                pass
            else:
                alert_type = ""
                
        # 7. Draw HUD telemetry on the frame
        hud_color = (0, 255, 255)  # Cyan/Yellow
        if alert_type:
            hud_color = (0, 0, 255)  # Red warning
            
        cv2.putText(frame, "SECURITY AI MONITORING", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, hud_color, 2)
        cv2.putText(frame, f"Intensity: {intensity:.1f}% (Thresh: {config.MOTION_INTENSITY_THRESHOLD}%)", (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Speed: {delta_speed:.1f} px/f (Thresh: {config.MOTION_SPEED_THRESHOLD})", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Frequency: {frequency} peaks/{config.MOTION_FREQUENCY_WINDOW_SEC}s", (15, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if alert_type:
            cv2.rectangle(frame, (10, 5), (width - 10, height - 10), (0, 0, 255), 3)
            cv2.putText(frame, f"ALERT: {alert_type}", (15, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
        return frame, abnormal_detected, alert_type
