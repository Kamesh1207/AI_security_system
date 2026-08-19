import os
import json
import time
import threading
from flask import Flask, render_template, Response, send_from_directory, jsonify, request
from camera_handler import CameraHandler
from serial_handler import SerialHandler
from intrusion_handler import IntrusionHandler
import config

# Create Flask application
app = Flask(__name__)

# System state database
system_state = {
    "system_status": "MONITORING",
    "motion_detected": False,
    "rfid_status": "IDLE",
    "password_status": "",
    "door_locked": True,
    "sound_value": 0,
    "alarm_active": False,
    "latest_incident": None,
    "latest_image": None,
    "hardware_online": False
}

# Instantiate handlers
camera_handler = CameraHandler()
intrusion_handler = IntrusionHandler(camera_handler)
serial_handler = None

# Thread lock for state modifications
state_lock = threading.Lock()

def update_state(key, value):
    with state_lock:
        system_state[key] = value

def get_recent_logs(limit=12):
    """
    Combines, parses, and sorts the last N lines from all security logs.
    """
    all_logs = []
    log_files = {
        "ACCESS": config.ACCESS_LOG_FILE,
        "INTRUSION": config.INTRUSION_LOG_FILE,
        "MOTION": config.MOTION_LOG_FILE,
        "SOUND": config.SOUND_LOG_FILE
    }
    
    for category, filepath in log_files.items():
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        line = line.strip()
                        if line:
                            # Extract timestamp and message
                            # Line format: [YYYY-MM-DD HH:MM:SS] Message
                            if line.startswith("[") and "]" in line:
                                ts_part, msg_part = line.split("]", 1)
                                timestamp = ts_part[1:].strip()
                                message = msg_part.strip()
                                all_logs.append({
                                    "timestamp": timestamp,
                                    "category": category,
                                    "message": message
                                })
            except Exception as e:
                print(f"[SERVER ERROR] Error reading log {filepath}: {e}")
                
    # Sort combined logs by timestamp descending (newest first)
    all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return all_logs[:limit]

def handle_hardware_status(online: bool):
    """
    Callback fired by SerialHandler whenever the hardware connection state changes.
    When offline, reset all sensor telemetry to safe defaults so the dashboard
    never shows stale / fake values.
    """
    with state_lock:
        system_state["hardware_online"] = online
        if not online:
            # Reset all sensor readings to neutral defaults
            system_state["motion_detected"] = False
            system_state["rfid_status"] = "IDLE"
            system_state["password_status"] = ""
            system_state["door_locked"] = True
            system_state["sound_value"] = 0
            system_state["system_status"] = "MONITORING"
    if online:
        print("[SYSTEM] Hardware ONLINE — real sensor data active.")
    else:
        print("[SYSTEM] Hardware OFFLINE — telemetry held at safe defaults.")

def handle_serial_event(event_name, data):
    """
    Central router for all events arriving from the ESP32.
    """
    print(f"[SYSTEM EVENT] Routing event {event_name} (data: {data})")
    
    if event_name == "MOTION_DETECTED":
        is_detected = (data == "TRUE")
        update_state("motion_detected", is_detected)
        
        # Adjust general system status text
        if is_detected:
            update_state("system_status", "ACCESS REQUEST DETECTED")
        else:
            # Only reset status back to MONITORING if we're not locked in auth states
            with state_lock:
                current_status = system_state["system_status"]
            if current_status == "ACCESS REQUEST DETECTED":
                update_state("system_status", "MONITORING")
                
    elif event_name == "RFID_SUCCESS":
        update_state("rfid_status", f"AUTHORIZED: {data}")
        update_state("system_status", "ENTER PASSWORD")
        update_state("password_status", "[AWAITING INPUT]")
        
    elif event_name == "RFID_FAILED":
        update_state("rfid_status", f"REJECTED: {data}")
        update_state("system_status", "ACCESS DENIED")
        intrusion_handler.handle_failed_rfid(data)
        
    elif event_name == "PASSWORD_INPUT":
        # Data contains masked characters, e.g. "***"
        if data == "":
            update_state("password_status", "[AWAITING INPUT]")
        else:
            update_state("password_status", data)
            
    elif event_name == "ACCESS_GRANTED":
        update_state("system_status", "ACCESS GRANTED")
        update_state("rfid_status", "IDLE")
        update_state("password_status", "")
        intrusion_handler.handle_access_granted()
        
    elif event_name == "ACCESS_DENIED":
        update_state("system_status", "ACCESS DENIED")
        update_state("rfid_status", "IDLE")
        update_state("password_status", "")
        intrusion_handler.handle_failed_password()
        
    elif event_name == "DOOR_UNLOCKED":
        update_state("door_locked", False)
        update_state("system_status", "DOOR UNLOCKED")
        
    elif event_name == "DOOR_LOCKED":
        update_state("door_locked", True)
        update_state("system_status", "MONITORING")
        
    elif event_name == "SOUND_LEVEL":
        # Continuous sound level telemetry (every 500ms from ESP32)
        try:
            val = int(data)
        except ValueError:
            val = 0
        update_state("sound_value", val)

    elif event_name == "LOUD_SOUND":
        try:
            val = int(data)
        except ValueError:
            val = 0
        update_state("sound_value", val)
        intrusion_handler.handle_loud_sound(val)

def handle_abnormal_motion(alert_type):
    """
    Callback fired from the camera handler when computer vision detects abnormal motion.
    """
    update_state("system_status", "ABNORMAL ACTIVITY DETECTED")
    intrusion_handler.handle_abnormal_motion(alert_type)

# Setup camera abnormal motion link
camera_handler.abnormal_motion_callback = handle_abnormal_motion

# ==========================================
# FLASK FLIGHT PATHS / ROUTES
# ==========================================

@app.route('/')
def index():
    # Use standard Flask page render
    return render_template('dashboard.html')

def gen_video_stream():
    """
    Video streaming generator function (MJPEG).
    """
    while True:
        frame_bytes = camera_handler.get_latest_jpeg()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)  # 20 FPS stream throttler

@app.route('/video_feed')
def video_feed():
    return Response(gen_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream-events')
def stream_events():
    """
    Server-Sent Events (SSE) channel sending structured state frames to the client.
    """
    def event_stream():
        while True:
            # Snapshot of current system state
            with state_lock:
                state_copy = system_state.copy()
            
            # Enrich state with live threat indicators
            state_copy["alarm_active"] = intrusion_handler.alarm_active
            state_copy["latest_incident"] = intrusion_handler.latest_incident
            state_copy["latest_image"] = camera_handler.get_latest_captured_image()
            state_copy["recent_logs"] = get_recent_logs()
            state_copy["hardware_online"] = system_state.get("hardware_online", False)
            
            yield f"data: {json.dumps(state_copy)}\n\n"
            time.sleep(0.5)  # Stream refresh rate: 500ms
            
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/captured_images/<filename>')
def serve_image(filename):
    return send_from_directory(config.CAPTURED_IMAGES_DIR, filename)

@app.route('/api/logs/<log_type>')
def get_log_file(log_type):
    filepaths = {
        "access": config.ACCESS_LOG_FILE,
        "intrusion": config.INTRUSION_LOG_FILE,
        "motion": config.MOTION_LOG_FILE,
        "sound": config.SOUND_LOG_FILE
    }
    
    filepath = filepaths.get(log_type.lower())
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "Log file not found"}), 404
        
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset-alarm', methods=['POST'])
def reset_alarm():
    intrusion_handler.reset_alarm()
    update_state("system_status", "MONITORING")
    return jsonify({"status": "success", "message": "Alarm status successfully reset."})

# /api/mock-event removed — no simulation mode

def start_server():
    # 1. Start the camera processing thread
    camera_handler.start()
    
    # 2. Start serial monitor thread (no mock mode — real hardware only)
    global serial_handler
    serial_handler = SerialHandler(
        event_callback=handle_serial_event,
        status_callback=handle_hardware_status
    )
    serial_handler.start()
    
    # 3. Launch Flask server on local address
    # (Threaded mode enabled to handle SSE requests and video streaming concurrently)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("[SERVER] Shutting down...")
        if serial_handler:
            serial_handler.stop()
        camera_handler.stop()
