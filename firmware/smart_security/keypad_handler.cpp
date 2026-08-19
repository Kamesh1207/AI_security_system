#include "keypad_handler.h"
#include "config.h"
#include "communication.h"

// Define static configuration variables
char KeypadHandler::keys[ROWS][COLS] = {
    {'1','2','3','A'},
    {'4','5','6','B'},
    {'7','8','9','C'},
    {'*','0','#','D'}
};

byte KeypadHandler::rowPins[ROWS] = {KEYPAD_ROW_1, KEYPAD_ROW_2, KEYPAD_ROW_3, KEYPAD_ROW_4};
byte KeypadHandler::colPins[COLS] = {KEYPAD_COL_1, KEYPAD_COL_2, KEYPAD_COL_3, KEYPAD_COL_4};

KeypadHandler::KeypadHandler() 
    : keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS) {
    currentInput = "";
    lastInputTime = 0;
}

void KeypadHandler::init() {
    // Keypad library configures internal GPIO states automatically
    reset();
    DEBUG_PRINTLN("[KEYPAD] Keypad Initialized on Rows: 13,12,14,27 | Cols: 26,25,33,32");
}

void KeypadHandler::reset() {
    currentInput = "";
    lastInputTime = millis();
}

bool KeypadHandler::update(bool& submitted) {
    char key = keypad.getKey();
    submitted = false;

    if (key != NO_KEY) {
        lastInputTime = millis(); // Refresh timeout timer on any key action
        DEBUG_PRINTLN("[KEYPAD] Key pressed: " + String(key));

        if (key == '#') {
            // Confirm/Submit password
            if (currentInput.length() > 0) {
                submitted = true;
            }
        } else if (key == '*') {
            // Clear current input
            currentInput = "";
            DEBUG_PRINTLN("[KEYPAD] Input Cleared");
            Communication::sendEvent("PASSWORD_INPUT", "");
        } else {
            // Append characters (support digits and alphabetical keys)
            currentInput += key;
            
            // Build a masked representation string
            String masked = "";
            for (unsigned int i = 0; i < currentInput.length(); i++) {
                masked += "*";
            }
            
            // Transmit masked update to the server
            Communication::sendEvent("PASSWORD_INPUT", masked);
        }
        return true;
    }
    return false;
}

String KeypadHandler::getPassword() {
    return currentInput;
}

bool KeypadHandler::isExpired() {
    // Check if the user took too long to complete the password input
    return (millis() - lastInputTime > inputTimeoutMs);
}
