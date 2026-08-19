#ifndef IR_HANDLER_H
#define IR_HANDLER_H

#include <Arduino.h>

class IRHandler {
private:
    uint8_t pin;
    bool lastDebouncedState;
    bool lastFlickerState;
    unsigned long lastDebounceTime;
    unsigned long debounceDelay;

public:
    IRHandler(uint8_t sensorPin);
    void init();
    bool isObjectDetected(); // Returns true if an object is present
};

#endif // IR_HANDLER_H
