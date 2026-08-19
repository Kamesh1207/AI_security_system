#include "rfid_handler.h"
#include "config.h"

RFIDHandler::RFIDHandler(uint8_t sdaPin, uint8_t rstPin)
    : mfrc522(sdaPin, rstPin) {
  lastScanTime = 0;
}

void RFIDHandler::init() {
  // Explicitly initialize SPI pins for ESP32 VSPI port
  SPI.begin(RFID_SCK_PIN, RFID_MISO_PIN, RFID_MOSI_PIN, RFID_SDA_PIN);

  // Initialize MFRC522 module
  mfrc522.PCD_Init();

  // Quick test to ensure reader communication is operational
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  DEBUG_PRINT("[RFID] MFRC522 Version: 0x");
  if (DEBUG_MODE) {
    Serial.println(v, HEX);
  }

  DEBUG_PRINTLN("[RFID] RFID Reader Initialized");
}

bool RFIDHandler::pollCard(String &uidOut) {
  unsigned long currentTime = millis();
  if (currentTime - lastScanTime < scanCooldownMs) {
    return false;
  }

  // Check if new card is present
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return false;
  }

  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return false;
  }

  lastScanTime = currentTime;

  // Convert UID bytes to Hex string
  uidOut = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uidOut += "0";
    }
    uidOut += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidOut.toUpperCase();

  DEBUG_PRINTLN("[RFID] Card Scanned. UID: " + uidOut);

  // Halt PICC and stop encryption to allow reading again
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  return true;
}

bool RFIDHandler::isAuthorized(const String &uid) {

  DEBUG_PRINTLN("===== AUTH DEBUG START =====");

  String cleanUID = uid;
  cleanUID.trim();
  cleanUID.toUpperCase();

  DEBUG_PRINT("SCANNED UID: ");
  DEBUG_PRINTLN(cleanUID);

  for (int i = 0; i < NUM_AUTHORIZED_UIDS; i++) {

    String authorizedUID = AUTHORIZED_UIDS[i];

    authorizedUID.trim();
    authorizedUID.toUpperCase();

    DEBUG_PRINT("AUTHORIZED UID: ");
    DEBUG_PRINTLN(authorizedUID);

    DEBUG_PRINT("UID LENGTH: ");
    DEBUG_PRINTLN(cleanUID.length());

    DEBUG_PRINT("AUTH LENGTH: ");
    DEBUG_PRINTLN(authorizedUID.length());

    if (cleanUID == authorizedUID) {

      DEBUG_PRINTLN("MATCH FOUND");
      return true;
    }
  }

  DEBUG_PRINTLN("NO MATCH FOUND");
  return false;
}
