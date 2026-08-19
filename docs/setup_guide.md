# Setup Guide - AI Smart Secure Access System

This document outlines the step-by-step procedure to set up the software environment, compile/upload the ESP32 firmware, and run the PC Flask security dashboard.

---

## 1. Prerequisites

Ensure you have the following installed on your Linux Ubuntu system:
- Python 3.8 or higher
- Python pip and venv packages
- Arduino CLI

---

## 2. PC Security Server Setup

Navigate to the project root directory and follow these steps to initialize the Python environment:

### Step 2.1: Create a Virtual Environment
```bash
python3 -m venv venv
```

### Step 2.2: Activate the Virtual Environment
```bash
source venv/bin/activate
```

### Step 2.3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2.4: Configure Serial Port
Open `pc_server/config.py` and verify that the `SERIAL_PORT` variable matches your ESP32's connection port (usually `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux). 

Give current user read/write access to the serial interface:
```bash
sudo usermod -a -G dialout $USER
```
*(Note: You will need to log out and log back in for this change to take effect).*

### Step 2.5: Run the Server
```bash
python pc_server/app.py
```
Open your web browser and go to `http://localhost:5000` to view the surveillance dashboard.

---

## 3. ESP32 Firmware Compilation & Upload

We compile and flash the firmware using the **Arduino CLI** inside the terminal.

### Step 3.1: Install Arduino CLI Libraries
Make sure the dependencies are installed (already present on this system):
```bash
arduino-cli lib install "MFRC522"
arduino-cli lib install "Keypad"
```

### Step 3.2: Compile the Code
Navigate to the project root and run the compile command:
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_security/
```
*(Replace `esp32:esp32:esp32` with your board's FQBN if using a specialized board module like NodeMCU, e.g., `esp32:esp32:esp32da`).*

### Step 3.3: Flash/Upload to the ESP32 Board
Connect your ESP32 board to the USB port of your laptop, and run:
```bash
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 firmware/smart_security/
```
*(Ensure the port matches the connected USB device).*
