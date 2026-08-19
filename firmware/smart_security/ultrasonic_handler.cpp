#include "ultrasonic_handler.h"
#include "config.h"

UltrasonicHandler::UltrasonicHandler(uint8_t trig, uint8_t echo) 
    : trigPin(trig), echoPin(echo), pollTimer(SENSOR_POLL_INTERVAL_MS) {
    lastDistanceCm = 999.0; // Initialize with a large distance
}

void UltrasonicHandler::init() {
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
    digitalWrite(trigPin, LOW);
    pollTimer.reset();
    DEBUG_PRINTLN("[ULTRASONIC] Ultrasonic Sensor Initialized on TRIG:" + String(trigPin) + " ECHO:" + String(echoPin));
}

float UltrasonicHandler::readDistanceCm() {
    if (pollTimer.isExpired()) {
        // Trigger pulse
        digitalWrite(trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);

        // Read echo pulse with a 25000us timeout (~4.25 meters max)
        long duration = pulseIn(echoPin, HIGH, 25000);

        if (duration == 0) {
            // Timeout or sensor reading error
            lastDistanceCm = 999.0;
        } else {
            // Speed of sound: 343 m/s -> 0.0343 cm/us. Distance = (duration * 0.0343) / 2
            float calculatedDistance = duration * 0.01715;

            // Apply a simple low-pass exponential filter to smooth the readings
            lastDistanceCm = (0.7 * calculatedDistance) + (0.3 * lastDistanceCm);
        }
        
        // Print raw reading in debug mode periodically
        // DEBUG_PRINTLN("[ULTRASONIC] Distance: " + String(lastDistanceCm) + " cm");
    }
    return lastDistanceCm;
}

bool UltrasonicHandler::isWithinThreshold(float thresholdCm) {
    float currentDist = readDistanceCm();
    // Verify distance is valid (not default 999) and below threshold
    return (currentDist > 2.0 && currentDist < thresholdCm);
}
