import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# SERIAL PORT SETTINGS
# ==========================================
SERIAL_PORT = "/dev/ttyUSB0"  # Default serial port on Linux, change to COMx on Windows
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 1.0          # Non-blocking read timeout (seconds)

# ==========================================
# DIRECTORIES FOR DATA STORAGE
# ==========================================
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CAPTURED_IMAGES_DIR = os.path.join(BASE_DIR, "captured_images")

# Ensure storage directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CAPTURED_IMAGES_DIR, exist_ok=True)

# Log file paths
ACCESS_LOG_FILE = os.path.join(LOGS_DIR, "access_logs.txt")
INTRUSION_LOG_FILE = os.path.join(LOGS_DIR, "intrusion_logs.txt")
MOTION_LOG_FILE = os.path.join(LOGS_DIR, "motion_logs.txt")
SOUND_LOG_FILE = os.path.join(LOGS_DIR, "sound_logs.txt")

# ==========================================
# WEBCAM & IMAGE SETTINGS
# ==========================================
CAMERA_INDEX = 0             # Index of the laptop webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ==========================================
# CV MOTION DETECTION PARAMETERS
# ==========================================
# Background subtractor history
BG_HISTORY = 100
BG_VAR_THRESHOLD = 25

# Min contour area to consider as motion (pixels)
MIN_MOTION_AREA = 1000

# Speed Threshold: pixels/frame displacement of the centroid
MOTION_SPEED_THRESHOLD = 45.0

# Intensity Threshold: % of screen covered by motion
MOTION_INTENSITY_THRESHOLD = 15.0

# Frequency Threshold: Number of motion peak counts in a sliding window
MOTION_FREQUENCY_THRESHOLD = 4
MOTION_FREQUENCY_WINDOW_SEC = 5.0

# Cooldown to report abnormal movement alerts (seconds)
ABNORMAL_MOTION_COOLDOWN = 4.0
