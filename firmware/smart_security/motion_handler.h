#ifndef MOTION_HANDLER_H
#define MOTION_HANDLER_H

#include <Arduino.h>
#include "ir_handler.h"
#include "ultrasonic_handler.h"
#include "utils.h"

class MotionHandler {
private:
    IRHandler& ir;
    UltrasonicHandler& ultrasonic;
    bool lastMotionState;
    unsigned long lastDetectionTime;
    const unsigned long motionHoldTimeMs = 3000; // Hold the detection state active for 3 seconds minimum

public:
    MotionHandler(IRHandler& irSensor, UltrasonicHandler& ultrasonicSensor);
    void init();
    bool update(); // Returns the current debounced motion status. Sends events on state changes.
    bool isMotionActive();
};

#endif // MOTION_HANDLER_H
