#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#include <Arduino.h>

class Communication {
public:
    static void init();
    static void sendEvent(const String& eventName, const String& data);
    static void sendEvent(const String& eventName);
};

#endif // COMMUNICATION_H
