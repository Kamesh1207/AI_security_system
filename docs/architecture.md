# System Architecture - AI Smart Security System

This document outlines the detailed system architecture, software layout, and operational flow for the AI Smart Secure Access & Intrusion Detection System.

---

## 1. Hardware-Software Partitioning

The system divides responsibilities between local embedded hardware and an edge-computing server to ensure maximum response speeds and efficiency:

```
+-----------------------------------+             +-----------------------------------+
|       ESP32 Microcontroller       |             |         PC Security Server        |
+-----------------------------------+             +-----------------------------------+
| - Reads physical sensors          |             | - Captures laptop webcam stream  |
| - Controls locks (Relay output)   |  Serial Link| - Processes OpenCV computer vision|
| - Validates RFID scans locally    |  ---------> | - Runs abnormal motion analysis   |
| - Manages Keypad entry & timeouts |             | - Drives Flask web-dashboard      |
| - Sends raw state change events   |             | - Stores system log files         |
+-----------------------------------+             +-----------------------------------+
```

---

## 2. ESP32 Non-Blocking State Machine

The firmware runs a central cooperative state machine. Blocking routines such as `delay()` or blocking sensor polling loop iterations are strictly avoided in favor of `millis()` checks:

* **Idle Monitoring (`STATE_IDLE`)**:
  Polls IR and Ultrasonic sensors every 100ms. If an obstacle appears or distance drops below 50cm, broadcasts `MOTION_DETECTED:TRUE` and transitions to:
* **Human Detected (`STATE_HUMAN_DETECTED`)**:
  Awaits card scanning on the MFRC522 SPI RFID module. If a valid card matches, sends `RFID_SUCCESS:<UID>` and transitions to Password Auth. If an invalid card is read, sends `RFID_FAILED:<UID>` and returns to Idle. Times out to Idle after 10 seconds if no card is read.
* **Password Authentication (`STATE_PASSWORD_AUTH`)**:
  Enables Keypad scanner. Standard keys (0-9, letters) append to password buffer and transmit masked updates (`PASSWORD_INPUT:***`). `*` clears inputs. `#` submits the PIN code. Valid passwords trigger `ACCESS_GRANTED:TRUE` and transition to Door Unlocked. Invalid PINs trigger `ACCESS_DENIED:TRUE` and return to Idle. Times out to Idle after 15 seconds of inactivity.
* **Door Unlocked State (`STATE_DOOR_UNLOCKED`)**:
  Powers the Relay high (unlocked door) and broadcasts `DOOR_UNLOCKED`. An internal timer waits 5 seconds, then powers the Relay low (locked), broadcasts `DOOR_LOCKED`, and resets the state machine back to Idle.

---

## 3. PC Server Components

The Flask backend is organized as multi-threaded modular services:

* **Serial Handler (`serial_handler.py`)**:
  Spawns a daemon thread monitoring the virtual COM serial port. Decodes strings into `(Event Name, Data)` pairs, updates global states, and routes callbacks to the intrusion controller. Integrates a mockup mode that generates events if the board is disconnected.
* **Camera Handler & CV (`camera_handler.py` & `motion_detection.py`)**:
  Operates a video thread querying frame feeds from the system's webcam. Runs frames through the `MotionDetector` utility, overlaying warning boundaries, intensity ratios, displacement rates, and frequencies. When abnormal flags raise, it captures JPEG snapshots stored in `captured_images/` with timestamp suffixes. Falls back to generating a simulated cyber-security canvas if no camera device is connected.
* **Intrusion Handler (`intrusion_handler.py`)**:
  Listens for critical events (bad cards, failed passwords, high noise, abnormal motions) to activate system-wide alarms and trigger snapshot grabs.
* **Flask Web App & SSE (`app.py`)**:
  Binds standard HTTP routes. Utilizes a Server-Sent Events (SSE) `/stream-events` connection to push live system state, alarm indicators, active metrics, and log queues to the HTML front-end every 500ms.

---

## 4. Computer Vision Motion Analysis

The computer vision pipeline is lightweight and relies on standard OpenCV algorithms:

1. **Preprocessing**: Grayscale conversion followed by `cv2.GaussianBlur` to suppress noise.
2. **Frame Differencing**: Computes `cv2.absdiff(frame_n-1, frame_n)` to highlight fast structural changes.
3. **Background Subtraction**: Uses MOG2 algorithm to separate permanent background components from moving foreground components.
4. **Contour Extraction**: Applies bounding rectangles around active pixel blocks.
   * **Intensity Calculation**: Computes the percentage of white foreground pixels over the total frame area.
   * **Speed Calculation**: Tracks the displacement of the centroid coordinates of the largest contour between consecutive frames.
   * **Frequency Tracking**: Maintains a list of motion peaks within a sliding 5-second window.
5. **Abnormal Motion Classification**:
   * *Sudden Fast Movement*: Triggered if displacement speed spikes past 45 pixels/frame.
   * *Excessive Motion*: Triggered if the active pixel ratio surpasses 15%.
   * *Suspicious Repeated Motion*: Triggered if the movement frequency exceeds 4 peaks within the sliding window.
   * *Abnormal Pattern*: Triggered if a speed spike exceeds 4x the rolling historical average.
