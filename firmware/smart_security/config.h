#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ==========================================
// SYSTEM SETTINGS
// ==========================================
#define SERIAL_BAUD_RATE 115200
#define DEBUG_MODE true

// Debug logging macros
#define DEBUG_PRINT(x)                                                         \
  do {                                                                         \
    if (DEBUG_MODE)                                                            \
      Serial.print(x);                                                         \
  } while (0)
#define DEBUG_PRINTLN(x)                                                       \
  do {                                                                         \
    if (DEBUG_MODE)                                                            \
      Serial.println(x);                                                       \
  } while (0)

// ==========================================
// PIN CONFIGURATIONS
// ==========================================

// RFID MFRC522 (SPI)
#define RFID_SDA_PIN 5
#define RFID_SCK_PIN 18
#define RFID_MOSI_PIN 23
#define RFID_MISO_PIN 19
#define RFID_RST_PIN 22

// Keypad (4x4 Matrix)
// Rows: Pin 13, 12, 14, 27
// Cols: Pin 26, 25, 33, 32
#define KEYPAD_ROW_1 13
#define KEYPAD_ROW_2 12
#define KEYPAD_ROW_3 14
#define KEYPAD_ROW_4 27
#define KEYPAD_COL_1 26
#define KEYPAD_COL_2 25
#define KEYPAD_COL_3 33
#define KEYPAD_COL_4 32

// Ultrasonic Sensor
#define ULTRASONIC_TRIG_PIN 4
#define ULTRASONIC_ECHO_PIN 2

// IR Sensor (Active HIGH or LOW - debounced)
#define IR_SENSOR_PIN 15

// Sound Sensor (Analog Input)
#define SOUND_SENSOR_PIN 34

// Relay Module
#define RELAY_PIN 21
#define RELAY_ACTIVE_STATE LOW // Set to LOW if using an Active-Low relay

// ==========================================
// SENSOR THRESHOLDS & TIMEOUTS
// ==========================================
#define ULTRASONIC_DIST_THRESHOLD_CM 50.0 // Distance to trigger human detection
#define SOUND_THRESHOLD_ADC 1500 // Analog sound peak threshold (out of 4095)
#define SOUND_COOLDOWN_MS 2000   // Rate limit sound reports (ms)

#define HUMAN_DETECTION_TIMEOUT_MS                                             \
  10000 // Return to idle if no RFID scanned after detection (10s)
#define PASSWORD_ENTRY_TIMEOUT_MS                                              \
  15000                               // Return to idle if keypad inactive (15s)
#define RELAY_UNLOCK_DURATION_MS 5000 // Keep door unlocked (5s)

#define SENSOR_POLL_INTERVAL_MS 100 // Poll IR/Ultrasonic every 100ms
#define SOUND_POLL_INTERVAL_MS 10   // Poll sound more frequently for peaks
#define SOUND_REPORT_INTERVAL_MS 500 // Report sound level to PC every 500ms

// ==========================================
// AUTHORIZATION DATABASE (MOCK)
// ==========================================
// Hardcoded authorized RFID UIDs
const int NUM_AUTHORIZED_UIDS = 2;
const String AUTHORIZED_UIDS[NUM_AUTHORIZED_UIDS] = {"BC608D04", "EAC0D405"};
// Hardcoded authorized keypad password
const String AUTHORIZED_PASSWORD = "1234";

// ==========================================
// SYSTEM STATES
// ==========================================
enum SystemState {
  STATE_IDLE,
  STATE_HUMAN_DETECTED,
  STATE_PASSWORD_AUTH,
  STATE_DOOR_UNLOCKED
};

#endif // CONFIG_H
