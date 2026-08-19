# Troubleshooting Guide - AI Smart Security System

This document outlines common issues encountered during the installation, wiring, compilation, or execution of the Smart Security System, and details steps to resolve them.

---

## 1. Serial Port / Communication Issues

### Issue: "Permission Denied" when opening serial port on Linux
* **Cause**: Linux requires specific group memberships to access USB TTY devices.
* **Solution**: Add your user to the dialout group and restart your terminal:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
  After running this, log out of your Linux session and log back in, or run `newgrp dialout` in your shell.

### Issue: "Port is busy" or "Device or resource busy"
* **Cause**: Another program (like Serial Monitor, another instance of the Flask app, or Arduino IDE) has opened the serial port, blocking other applications.
* **Solution**: Close any software that is listening to the serial port. Unplug and replug the ESP32 USB cable if the port remains locked.

### Issue: No data is displayed, or garbage characters appear
* **Cause**: Baud rate mismatch.
* **Solution**: Check that `SERIAL_BAUD_RATE` in `config.h` matches `SERIAL_BAUD` in `config.py` (both should be set to `115200`).

---

## 2. Hardware / Sensor Failures

### Issue: RFID Card does not scan
* **Cause 1**: The RFID reader runs on 3.3V and consumes significant current during scans. If wired to a low-current pin, it will fail.
  * **Solution**: Ensure SDA and RST lines are connected to correct GPIOs (5 and 22). Verify MFRC522 is connected to the 3.3V power output of the ESP32, and ensure the USB cable supplying the ESP32 is capable of delivering adequate power.
* **Cause 2**: Improper SPI connection.
  * **Solution**: Check standard SPI lines SCK (GPIO 18), MISO (GPIO 19), MOSI (GPIO 23).

### Issue: Keypad inputs are missed or register multiple times
* **Cause**: Loose wire connections or bouncing on key matrices.
* **Solution**: Verify all 8 keypad GPIO wires are inserted firmly. Avoid long jumper wires which increase capacitance and noise on scanning lines.

### Issue: False motion triggers on Ultrasonic or IR
* **Cause**: Voltage spikes or reflection.
* **Solution**: Ensure the Ultrasonic ECHO line is scaled down to 3.3V using a voltage divider (resistors). Check if there is an obstacle too close to the sensor. Clean the lens of the IR obstacle sensor.

---

## 3. Python / OpenCV Server Issues

### Issue: OpenCV cannot open the webcam
* **Cause**: The webcam is either already in use, blocked by OS permissions, or the configured camera index is incorrect.
* **Solution**: 
  1. Open `pc_server/config.py` and verify `CAMERA_INDEX`. Usually `0` is the integrated webcam. Change it to `1` or `2` if using an external USB webcam.
  2. Close any other software using the camera (Zoom, Teams, Discord).
  3. Ensure OpenCV is installed with GUI support: `pip install opencv-python`.
  4. Note that if no webcam is available, the backend automatically transitions to **Simulation mode**, which generates a simulated video feed so that the system remains testable.

### Issue: Flask dashboard does not receive updates
* **Cause**: The browser blocked the Server-Sent Events (SSE) stream or serial reader failed to start.
* **Solution**: Open the browser's developer console (F12) and inspect the console logs. Verify if there are any network errors or blocked connections. Ensure JavaScript is enabled.
