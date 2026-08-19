#include "ir_handler.h"
#include "config.h"

IRHandler::IRHandler(uint8_t sensorPin) {
    pin = sensorPin;
    lastDebouncedState = false;
    lastFlickerState = false;
    lastDebounceTime = 0;
    debounceDelay = 50; // 50ms debounce time
}

void IRHandler::init() {
    pinMode(pin, INPUT);
    DEBUG_PRINTLN("[IR] IR Sensor Initialized on GPIO " + String(pin));
}

bool IRHandler::isObjectDetected() {
    // Read the sensor value (standard IR obstacles are active LOW)
    // LOW = Object detected, HIGH = Clear path
    bool rawState = (digitalRead(pin) == LOW); 

    if (rawState != lastFlickerState) {
        lastDebounceTime = millis();
        lastFlickerState = rawState;
    }

    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (rawState != lastDebouncedState) {
            lastDebouncedState = rawState;
            if (lastDebouncedState) {
                DEBUG_PRINTLN("[IR] Motion Detected (Object Present)");
            } else {
                DEBUG_PRINTLN("[IR] Path Cleared");
            }
        }
    }

    return lastDebouncedState;
}
