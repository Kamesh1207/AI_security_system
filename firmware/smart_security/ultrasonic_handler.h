#ifndef ULTRASONIC_HANDLER_H
#define ULTRASONIC_HANDLER_H

#include <Arduino.h>
#include "utils.h"

class UltrasonicHandler {
private:
    uint8_t trigPin;
    uint8_t echoPin;
    float lastDistanceCm;
    NonBlockingTimer pollTimer;

public:
    UltrasonicHandler(uint8_t trig, uint8_t echo);
    void init();
    float readDistanceCm(); // Performs distance measurement (called at timer intervals)
    bool isWithinThreshold(float thresholdCm);
};

#endif // ULTRASONIC_HANDLER_H
