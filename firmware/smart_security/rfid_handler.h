#ifndef RFID_HANDLER_H
#define RFID_HANDLER_H

#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

class RFIDHandler {
private:
    MFRC522 mfrc522;
    unsigned long lastScanTime;
    const unsigned long scanCooldownMs = 1500; // Delay before scanning same/another card again

public:
    RFIDHandler(uint8_t sdaPin, uint8_t rstPin);
    void init();
    bool pollCard(String& uidOut); // Checks for card, returns true if scanned, stores UID
    bool isAuthorized(const String& uid); // Checks if UID is in the authorized list
};

#endif // RFID_HANDLER_H
