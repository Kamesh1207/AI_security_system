#ifndef SOUND_HANDLER_H
#define SOUND_HANDLER_H

#include <Arduino.h>
#include "utils.h"

class SoundHandler {
private:
    uint8_t pin;
    uint16_t threshold;
    unsigned long lastAlertTime;
    unsigned long cooldownDuration;
    NonBlockingTimer sampleTimer;
    NonBlockingTimer reportTimer;    // Timer for periodic level reporting
    uint16_t lastReportedValue;      // Last reported ADC value

public:
    SoundHandler(uint8_t sensorPin, uint16_t adcThreshold, unsigned long cooldownMs);
    void init();
    void update(); // Called inside loop, checks for peaks and reports levels
};

#endif // SOUND_HANDLER_H
