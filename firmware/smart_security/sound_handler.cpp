#include "sound_handler.h"
#include "communication.h"
#include "config.h"

SoundHandler::SoundHandler(uint8_t sensorPin, uint16_t adcThreshold, unsigned long cooldownMs)
    : pin(sensorPin), threshold(adcThreshold), cooldownDuration(cooldownMs),
      sampleTimer(SOUND_POLL_INTERVAL_MS), reportTimer(SOUND_REPORT_INTERVAL_MS) {
    lastAlertTime = 0;
    lastReportedValue = 0;
}

void SoundHandler::init() {
    pinMode(pin, INPUT);
    sampleTimer.reset();
    reportTimer.reset();
    DEBUG_PRINTLN("[SOUND] Sound Sensor Initialized on GPIO " + String(pin) + " with threshold " + String(threshold));
}

void SoundHandler::update() {
    // Poll the sound sensor at the fast sample interval
    if (sampleTimer.isExpired()) {
        int rawValue = analogRead(pin);

        // Track latest value for periodic reporting
        lastReportedValue = rawValue;

        // Check if raw value exceeds threshold and cooldown has passed
        if (rawValue > threshold) {
            unsigned long currentTime = millis();
            if (currentTime - lastAlertTime >= cooldownDuration) {
                lastAlertTime = currentTime;
                
                // Format event and transmit to PC
                DEBUG_PRINTLN("[SOUND] Peak Detected: " + String(rawValue));
                Communication::sendEvent("LOUD_SOUND", String(rawValue));
            }
        }
    }

    // Periodically report the current sound level (every 500ms)
    if (reportTimer.isExpired()) {
        Communication::sendEvent("SOUND_LEVEL", String(lastReportedValue));
    }
}
