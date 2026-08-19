#ifndef RELAY_HANDLER_H
#define RELAY_HANDLER_H

#include <Arduino.h>

class RelayHandler {
private:
    uint8_t pin;
    bool activeState;
    bool isUnlockedState;
    unsigned long unlockStartTime;
    unsigned long unlockDurationMs;

public:
    RelayHandler(uint8_t relayPin, bool activeHigh, unsigned long durationMs);
    void init();
    void unlock();
    void lock();
    void update(); // Non-blocking check to lock after duration
    bool isUnlocked();
};

#endif // RELAY_HANDLER_H
