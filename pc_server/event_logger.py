import os
import datetime
from threading import Lock
import config

# File writing locks to prevent race conditions from multiple threads
_access_lock = Lock()
_intrusion_lock = Lock()
_motion_lock = Lock()
_sound_lock = Lock()

def _write_log(filepath, message, lock):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_entry = f"[{timestamp}] {message}\n"
    
    with lock:
        try:
            with open(filepath, "a") as f:
                f.write(formatted_entry)
            print(f"[LOG] {message}")  # Console duplicate
        except Exception as e:
            print(f"[ERROR] Failed to write to log file {filepath}: {e}")

def log_access(message):
    _write_log(config.ACCESS_LOG_FILE, message, _access_lock)

def log_intrusion(message):
    _write_log(config.INTRUSION_LOG_FILE, message, _intrusion_lock)

def log_motion(message):
    _write_log(config.MOTION_LOG_FILE, message, _motion_lock)

def log_sound(message):
    _write_log(config.SOUND_LOG_FILE, message, _sound_lock)
