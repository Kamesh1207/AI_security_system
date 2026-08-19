# Wiring Guide - ESP32 Smart Security Access Control

This document contains the wiring schematic and connection details for all modules integrated with the ESP32.

---

## 1. GPIO Pin Connection Table

| Device Module | Sensor Pin | ESP32 GPIO | Voltage Source | Description |
| :--- | :--- | :--- | :--- | :--- |
| **RFID MFRC522** | VCC | 3.3V | 3.3V | RFID power (do not connect to 5V!) |
| | GND | GND | GND | Ground |
| | RST | GPIO 22 | 3.3V Logic | Reset line |
| | MISO | GPIO 19 | 3.3V Logic | SPI Master In Slave Out |
| | MOSI | GPIO 23 | 3.3V Logic | SPI Master Out Slave In |
| | SCK | GPIO 18 | 3.3V Logic | SPI Clock |
| | SDA (SS) | GPIO 5 | 3.3V Logic | SPI Slave Select (Chip Select) |
| **Keypad 4x4** | Row 1 | GPIO 13 | 3.3V Logic | Keyboard matrix Row 1 |
| | Row 2 | GPIO 12 | 3.3V Logic | Keyboard matrix Row 2 |
| | Row 3 | GPIO 14 | 3.3V Logic | Keyboard matrix Row 3 |
| | Row 4 | GPIO 27 | 3.3V Logic | Keyboard matrix Row 4 |
| | Col 1 | GPIO 26 | 3.3V Logic | Keyboard matrix Column 1 |
| | Col 2 | GPIO 25 | 3.3V Logic | Keyboard matrix Column 2 |
| | Col 3 | GPIO 33 | 3.3V Logic | Keyboard matrix Column 3 |
| | Col 4 | GPIO 32 | 3.3V Logic | Keyboard matrix Column 4 |
| **Ultrasonic HC-SR04**| VCC | 5V | 5V | Sensor power |
| | TRIG | GPIO 4 | 5V Logic (O) | Trigger output |
| | ECHO | GPIO 2 | 3.3V Logic (I)*| Echo input (*Use 1k/2k resistor voltage divider) |
| | GND | GND | GND | Ground |
| **IR Obstacle** | VCC | 3.3V or 5V| 3.3V / 5V | Sensor power |
| | OUT | GPIO 15 | 3.3V Logic | Digital signal (LOW = object present) |
| | GND | GND | GND | Ground |
| **Sound Sensor** | VCC | 3.3V or 5V| 3.3V / 5V | Sensor power |
| | AO | GPIO 34 | Analog (0-3.3V)| Analog sensor peak reading (ADC Pin) |
| | GND | GND | GND | Ground |
| **Relay Module** | VCC | 5V | 5V | Relay coil power |
| | IN | GPIO 21 | 3.3V Logic | Signal input (HIGH = unlock / active) |
| | GND | GND | GND | Ground |

---

## 2. Detailed Connection Explanations

### RFID MFRC522 Reader
* **Power**: Connect **only** to the ESP32 **3.3V** rail. Connecting to 5V will burn the MFRC522 chip.
* **SPI interface**: Connected to the default VSPI pins of the ESP32 (SCK=18, MISO=19, MOSI=23). SDA (SS) is mapped to GPIO 5, and RST is mapped to GPIO 22.

### 4x4 Membrane Keypad
* Uses 8 pins directly connected to the ESP32 GPIOs. Row pins (13, 12, 14, 27) act as outputs, and Column pins (26, 25, 33, 32) act as inputs with internal pull-up resistors activated via the Keypad library.

### Ultrasonic Sensor (HC-SR04)
* **Echo Protection**: The HC-SR04 outputs a 5V echo pulse. While many ESP32 pins are 5V-tolerant, it is highly recommended to place a simple voltage divider on the ECHO line (GPIO 2) to scale the signal down to 3.3V:
  ```
  HC-SR04 ECHO Pin ----[ 1k Ohm Resistor ]----+---- ESP32 GPIO 2
                                               |
                                        [ 2k Ohm Resistor ]
                                               |
                                              GND
  ```

### Relay Connection Details
* **Control Side**: Connect VCC to 5V, GND to GND, and IN to GPIO 21.
* **Switching Side**: Connect your lock device to the **COM** (Common) and **NO** (Normally Open) terminals.
  * **Warning**: Do not use the NC (Normally Closed) terminal. This ensures that in the event of a power outage or system crash, the lock defaults to a secure (locked) state.
