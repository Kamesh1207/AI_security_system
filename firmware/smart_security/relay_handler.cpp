#include "relay_handler.h"
#include "communication.h"
#include "config.h"

RelayHandler::RelayHandler(uint8_t relayPin, bool activeHigh,
                           unsigned long durationMs) {

  pin = relayPin;

  activeState = activeHigh;

  unlockDurationMs = durationMs;

  isUnlockedState = false;

  unlockStartTime = 0;
}

void RelayHandler::init() {

  pinMode(pin, OUTPUT);

  // ACTIVE LOW RELAY:
  // HIGH = OFF
  // LOW = ON

  digitalWrite(pin, HIGH);

  isUnlockedState = false;

  DEBUG_PRINTLN("[RELAY] Relay Initialized OFF");
}

void RelayHandler::unlock() {

  if (!isUnlockedState) {

    isUnlockedState = true;

    unlockStartTime = millis();

    // TURN RELAY ON
    digitalWrite(pin, LOW);

    DEBUG_PRINTLN("[RELAY] Door Unlocked");

    Communication::sendEvent("DOOR_UNLOCKED");
  }
}

void RelayHandler::lock() {

  if (isUnlockedState) {

    isUnlockedState = false;

    // TURN RELAY OFF
    digitalWrite(pin, HIGH);

    DEBUG_PRINTLN("[RELAY] Door Locked");

    Communication::sendEvent("DOOR_LOCKED");
  }
}

void RelayHandler::update() {

  if (isUnlockedState) {

    if (millis() - unlockStartTime >= unlockDurationMs) {

      lock();
    }
  }
}

bool RelayHandler::isUnlocked() { return isUnlockedState; }