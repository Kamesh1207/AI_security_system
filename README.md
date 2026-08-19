# AI Smart Secure Access & Intrusion Detection System

A production-grade, modular, real-world embedded security system. The system utilizes an **ESP32 microcontroller** for local sensor polling, RFID validation, Keypad entries, and lock control (Relay module), communicating over a structured USB-serial link with a **Python Flask & OpenCV server** which performs live webcam capture, computer-vision based abnormal motion detection, sound peak analysis, and real-time dashboard visualization.

---

## Key Features

- **Cooperative State Machine**: Completely non-blocking ESP32 firmware using `millis()` timing.
- **Multi-Factor Authentication**: Card validation via SPI RFID MFRC522 followed by Keypad PIN entry.
- **Embedded Sensors**: Continuous polling of IR obstacle detection, Ultrasonic distance range, and Analog sound amplitude.
- **Relay Lock Interface**: Safe lock switching using COM/NO terminals, featuring a 5-second automatic re-lock timer.
- **Edge CV Motion Analytics**: Real-time frame analysis calculating motion intensity (percentage), movement speed (displacement), and frequency (peaks) to identify sudden, excessive, or repeated suspicious behaviors.
- **Automatic Incident Capture**: Automatically captures and stores timestamped evidence pictures upon unauthorized access, incorrect password, loud noises, or abnormal motion detection.
- **Sleek Dark Dashboard**: Real-time Server-Sent Events (SSE) updates, live surveillance view, sensor gauges, dynamic alarm warning banners, and logs feed.
- **Robust Hardware Simulation Fallback**: If the ESP32 board or the laptop webcam is not connected, the server automatically boots into simulation/demo mode to allow full testing of the web application.

---

## Folder Structure

```
AI_Smart_Security_System/
│
├── firmware/
│   └── smart_security/
│       ├── smart_security.ino      # Main loop & state machine
│       ├── config.h                # GPIOs, thresholds, user database
│       ├── rfid_handler.h/.cpp     # SPI RFID reader driver
│       ├── keypad_handler.h/.cpp   # Matrix keypad decoder
│       ├── relay_handler.h/.cpp    # Relay controller with timer
│       ├── ultrasonic_handler.h/.cpp # Ultrasonic non-blocking pulse
│       ├── ir_handler.h/.cpp       # IR obstacle debouncer
│       ├── sound_handler.h/.cpp    # Analog sound monitor
│       ├── communication.h/.cpp    # Serial protocol encoder
│       ├── motion_handler.h/.cpp   # Sensor coordinator
│       └── utils.h                 # Non-blocking timers
│
├── pc_server/
│   ├── app.py                      # Flask web server & SSE
│   ├── serial_handler.py           # Serial decoder & simulation loop
│   ├── camera_handler.py           # OpenCV webcam feed & snapshot capturer
│   ├── motion_detection.py         # CV movement speed/intensity/frequency
│   ├── intrusion_handler.py        # System alarm triggers & snaps
│   ├── event_logger.py             # Thread-safe log files writer
│   ├── config.py                   # PC parameters & thresholds
│   │
│   ├── templates/
│   │   └── dashboard.html          # Dark-themed HTML dashboard
│   │
│   └── static/
│       ├── style.css               # CSS stylesheet (glowing cards, glassmorphism)
│       ├── script.js               # Dashboard EventSource state listener
│       └── logo.png                # Security system logo
│
├── docs/
│   ├── setup_guide.md              # Installation & startup details
│   ├── wiring_guide.md             # Pin maps & resistor schematics
│   ├── architecture.md             # Partitioning & CV formulas
│   └── troubleshooting.md          # Diagnostic steps & permissions
│
├── requirements.txt                # Python package list
├── README.md                       # This documentation file
└── .gitignore                      # Git exclusion rules
```

---

## Quickstart

1. **Wiring**: Connect your sensors to the ESP32 according to the [Wiring Guide](docs/wiring_guide.md).
2. **Flash Firmware**: Compile and upload the firmware using Arduino CLI:
   ```bash
   arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_security/
   arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 firmware/smart_security/
   ```
3. **Run PC Server**: Set up the virtual environment, install requirements, and run the server:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python pc_server/app.py
   ```
4. **Open Dashboard**: Visit `http://localhost:5000` in your web browser.
