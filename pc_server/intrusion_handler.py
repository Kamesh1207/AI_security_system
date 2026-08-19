import event_logger

class IntrusionHandler:
    def __init__(self, camera_handler):
        self.camera = camera_handler
        self.alarm_active = False
        self.latest_incident = None

    def handle_failed_rfid(self, uid):
        message = f"FAILED LOGIN: Unauthorized RFID scan [UID: {uid}]"
        event_logger.log_access(message)
        event_logger.log_intrusion(message)
        
        # Trigger photo snapshot
        self.camera.capture_snapshot("RFID_FAILED")
        self.latest_incident = f"Unauthorized RFID: {uid}"
        self.alarm_active = True

    def handle_failed_password(self):
        message = "FAILED LOGIN: Incorrect keypad password entered"
        event_logger.log_access(message)
        event_logger.log_intrusion(message)
        
        # Trigger photo snapshot
        self.camera.capture_snapshot("ACCESS_DENIED")
        self.latest_incident = "Incorrect PIN code"
        self.alarm_active = True

    def handle_access_granted(self):
        message = "ACCESS GRANTED: Valid credentials validated"
        event_logger.log_access(message)
        
        # Take photo snapshot for audit log
        self.camera.capture_snapshot("ACCESS_GRANTED")
        self.alarm_active = False  # Reset alarm status upon valid entry
        self.latest_incident = None

    def handle_loud_sound(self, value):
        message = f"ALERT: High noise peak detected! Analog ADC value: {value}"
        event_logger.log_sound(message)
        
        # Trigger photo snapshot
        self.camera.capture_snapshot(f"LOUD_SOUND_ADC_{value}")

    def handle_abnormal_motion(self, alert_type):
        message = f"ALERT: Abnormal motion pattern identified! Pattern: {alert_type}"
        # Logged via camera_handler directly, but we link it to the incident state
        self.latest_incident = f"Abnormal Motion: {alert_type}"
        self.alarm_active = True

    def handle_intrusion(self):
        message = "ALERT: Intended intrusion detected! Motion active without authorization"
        event_logger.log_intrusion(message)
        self.camera.capture_snapshot("INTRUSION_ALERT")
        self.latest_incident = "Possible perimeter intrusion"
        self.alarm_active = True

    def reset_alarm(self):
        self.alarm_active = False
        self.latest_incident = None
        print("[INTRUSION] Alarm manually reset.")
