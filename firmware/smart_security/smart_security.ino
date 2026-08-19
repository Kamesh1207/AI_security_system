#include "communication.h"
#include "config.h"
#include "ir_handler.h"
#include "keypad_handler.h"
#include "motion_handler.h"
#include "relay_handler.h"
#include "rfid_handler.h"
#include "sound_handler.h"
#include "ultrasonic_handler.h"
#include "utils.h"

// Instantiate sensor and hardware handler objects
IRHandler irHandler(IR_SENSOR_PIN);
UltrasonicHandler ultrasonicHandler(ULTRASONIC_TRIG_PIN, ULTRASONIC_ECHO_PIN);
MotionHandler motionHandler(irHandler, ultrasonicHandler);
SoundHandler soundHandler(SOUND_SENSOR_PIN, SOUND_THRESHOLD_ADC,
                          SOUND_COOLDOWN_MS);
RFIDHandler rfidHandler(RFID_SDA_PIN, RFID_RST_PIN);
KeypadHandler keypadHandler;
RelayHandler relayHandler(RELAY_PIN, (RELAY_ACTIVE_STATE == HIGH),
                          RELAY_UNLOCK_DURATION_MS);

// State machine trackers
SystemState currentState = STATE_IDLE;
unsigned long stateTimer = 0;

void transitionTo(SystemState newState) {
  currentState = newState;
  stateTimer = millis();

  switch (currentState) {
  case STATE_IDLE:
    DEBUG_PRINTLN("[SYSTEM STATE] Entering IDLE MONITORING");
    break;
  case STATE_HUMAN_DETECTED:
    DEBUG_PRINTLN("[SYSTEM STATE] Entering HUMAN DETECTION (Awaiting RFID)");
    break;
  case STATE_PASSWORD_AUTH:
    DEBUG_PRINTLN(
        "[SYSTEM STATE] Entering PASSWORD AUTHENTICATION (Awaiting Keypad)");
    keypadHandler.reset();
    break;
  case STATE_DOOR_UNLOCKED:
    DEBUG_PRINTLN("[SYSTEM STATE] Entering DOOR UNLOCKED");
    break;
  }
}

void setup() {
  // 1. Initialize Communication Module (Serial Interface)
  Communication::init();

  // 2. Initialize all sub-hardware modules
  motionHandler.init();
  soundHandler.init();
  rfidHandler.init();
  keypadHandler.init();
  relayHandler.init();

  // 3. Set starting state
  transitionTo(STATE_IDLE);

  DEBUG_PRINTLN("[SYSTEM] Security System Startup Complete");
}

void loop() {

  // Always poll sound peaks and update the non-blocking relay timer
  soundHandler.update();
  relayHandler.update();

  // Execute state logic
  switch (currentState) {

  case STATE_IDLE: {

    // Update human detection sensors
    motionHandler.update();

    // Transition ONLY ONCE when motion is first detected
    if (motionHandler.isMotionActive() &&
        currentState != STATE_HUMAN_DETECTED) {

      transitionTo(STATE_HUMAN_DETECTED);
    }

    break;
  }

  case STATE_HUMAN_DETECTED: {
    // Check for card scan
    String scannedUID = "";
    if (rfidHandler.pollCard(scannedUID)) {
      if (rfidHandler.isAuthorized(scannedUID)) {
        Communication::sendEvent("RFID_SUCCESS", scannedUID);
        transitionTo(STATE_PASSWORD_AUTH);
      } else {
        Communication::sendEvent("RFID_FAILED", scannedUID);
        // Invalid card: Alert logged on server, reset immediately back to IDLE
        transitionTo(STATE_IDLE);
      }
      break;
    }

    // Timeout: return to IDLE if human has left or no scan for 10 seconds
    if (millis() - stateTimer > HUMAN_DETECTION_TIMEOUT_MS) {
      DEBUG_PRINTLN("[STATE TIMEOUT] No RFID scanned. Returning to IDLE.");
      transitionTo(STATE_IDLE);
    }
    break;
  }

  case STATE_PASSWORD_AUTH: {
    bool submitted = false;
    keypadHandler.update(submitted);

    if (submitted) {
      String enteredPassword = keypadHandler.getPassword();
      if (enteredPassword.equals(AUTHORIZED_PASSWORD)) {
        Communication::sendEvent("ACCESS_GRANTED", "TRUE");
        relayHandler.unlock();
        transitionTo(STATE_DOOR_UNLOCKED);
      } else {
        Communication::sendEvent("ACCESS_DENIED", "TRUE");
        // Failed attempt logged, return to IDLE
        transitionTo(STATE_IDLE);
      }
      break;
    }

    // Timeout: return to IDLE if keypad is inactive for 15 seconds
    if (keypadHandler.isExpired()) {
      DEBUG_PRINTLN("[STATE TIMEOUT] Keypad input expired. Returning to IDLE.");
      Communication::sendEvent("PASSWORD_INPUT", ""); // Clear state on server
      transitionTo(STATE_IDLE);
    }
    break;
  }

  case STATE_DOOR_UNLOCKED: {
    // Wait for door to auto-lock (monitored by relayHandler.update)
    if (!relayHandler.isUnlocked()) {
      transitionTo(STATE_IDLE);
    }
    break;
  }
  }
}
