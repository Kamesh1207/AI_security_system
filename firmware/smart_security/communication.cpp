#include "communication.h"
#include "config.h"

void Communication::init() {
    Serial.begin(SERIAL_BAUD_RATE);
    // Wait for serial to initialize
    unsigned long start = millis();
    while (!Serial && (millis() - start < 1000)) {
        delay(1);
    }
    DEBUG_PRINTLN("[COMM] Serial Communication Initialized");
}

void Communication::sendEvent(const String& eventName, const String& data) {
    Serial.print(eventName);
    Serial.print(":");
    Serial.println(data);
}

void Communication::sendEvent(const String& eventName) {
    Serial.println(eventName);
}
