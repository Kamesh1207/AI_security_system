#ifndef KEYPAD_HANDLER_H
#define KEYPAD_HANDLER_H

#include <Arduino.h>
#include <Keypad.h>

class KeypadHandler {
private:
    Keypad keypad;
    String currentInput;
    unsigned long lastInputTime;
    const unsigned long inputTimeoutMs = 15000; // Inactivity timeout

    static const byte ROWS = 4;
    static const byte COLS = 4;
    static char keys[ROWS][COLS];
    static byte rowPins[ROWS];
    static byte colPins[COLS];

public:
    KeypadHandler();
    void init();
    void reset();
    bool update(bool& submitted); // Returns true if there was activity, submitted is set true if '#' is pressed
    String getPassword();
    bool isExpired(); // Checks if password entry has timed out due to inactivity
};

#endif // KEYPAD_HANDLER_H
