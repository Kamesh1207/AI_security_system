#ifndef UTILS_H
#define UTILS_H

#include <Arduino.h>

class NonBlockingTimer {
private:
    unsigned long previousMillis;
    unsigned long interval;

public:
    NonBlockingTimer(unsigned long timerInterval) {
        interval = timerInterval;
        previousMillis = 0;
    }

    void setInterval(unsigned long newInterval) {
        interval = newInterval;
    }

    void reset() {
        previousMillis = millis();
    }

    bool isExpired() {
        if (millis() - previousMillis >= interval) {
            previousMillis = millis();
            return true;
        }
        return false;
    }

    bool checkWithoutReset() {
        return (millis() - previousMillis >= interval);
    }
};

#endif // UTILS_H
