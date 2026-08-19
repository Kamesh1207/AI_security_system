#include "motion_handler.h"
#include "communication.h"
#include "config.h"

MotionHandler::MotionHandler(IRHandler &irSensor,
                             UltrasonicHandler &ultrasonicSensor)
    : ir(irSensor), ultrasonic(ultrasonicSensor) {
  lastMotionState = false;
  lastDetectionTime = 0;
}

void MotionHandler::init() {
  ir.init();
  ultrasonic.init();
  DEBUG_PRINTLN("[MOTION] Motion Coordinator Initialized");
}

bool MotionHandler::update() {
  // Read raw sensor values
  bool irTriggered = ir.isObjectDetected();
  bool ultrasonicTriggered =
      ultrasonic.isWithinThreshold(ULTRASONIC_DIST_THRESHOLD_CM);
  bool rawDetection = irTriggered || ultrasonicTriggered;

  unsigned long currentTime = millis();

  // If raw detection occurs, refresh the hold timer
  if (rawDetection) {
    lastDetectionTime = currentTime;
  }

  // Determine current motion state based on hold timer
  bool currentMotionState = false;
  if (rawDetection || (currentTime - lastDetectionTime < motionHoldTimeMs)) {
    currentMotionState = true;
  }

  // Check for state transitions and broadcast events
  if (currentMotionState != lastMotionState) {
    lastMotionState = currentMotionState;
    if (lastMotionState) {
      DEBUG_PRINTLN("[MOTION] Human Presence Detected");
      Communication::sendEvent("MOTION_DETECTED", "TRUE");
    } else {
      DEBUG_PRINTLN("[MOTION] Human Presence Cleared");
    }
  }

  return lastMotionState;
}

bool MotionHandler::isMotionActive() { return lastMotionState; }
