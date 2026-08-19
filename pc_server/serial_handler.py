import serial
import time
import threading
import config
import event_logger

class SerialHandler:
    def __init__(self, port=config.SERIAL_PORT, baud=config.SERIAL_BAUD, event_callback=None,
                 status_callback=None):
        self.port = port
        self.baud = baud
        self.event_callback = event_callback
        self.status_callback = status_callback   # called with True/False when hw online state changes
        self.ser = None
        self.running = False
        self.thread = None
        self.hardware_online = False
        self.lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, name="SerialReaderThread", daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.ser = None
        self._set_hardware_online(False)
        print("[SERIAL] Serial handler stopped.")

    def _set_hardware_online(self, state: bool):
        """Update hardware_online flag and fire status_callback if state changed."""
        if self.hardware_online != state:
            self.hardware_online = state
            status_label = "ONLINE" if state else "OFFLINE"
            print(f"[SERIAL] Hardware status changed -> {status_label}")
            if self.status_callback:
                self.status_callback(state)

    def _try_open(self) -> bool:
        """Attempt to open the serial port. Returns True on success."""
        try:
            with self.lock:
                self.ser = serial.Serial(self.port, self.baud, timeout=config.SERIAL_TIMEOUT)
                self.ser.reset_input_buffer()
            print(f"[SERIAL] Connected to {self.port} at {self.baud} baud.")
            self._set_hardware_online(True)
            return True
        except Exception as e:
            print(f"[SERIAL] Cannot open {self.port}: {e}. Hardware OFFLINE.")
            self._set_hardware_online(False)
            return False

    def _read_loop(self):
        # Attempt initial connection
        while self.running and not self._try_open():
            time.sleep(3.0)   # Retry every 3 s until connected

        while self.running:
            try:
                with self.lock:
                    port_open = self.ser is not None and self.ser.is_open

                if not port_open:
                    self._set_hardware_online(False)
                    print("[SERIAL] Port closed — attempting reconnect...")
                    time.sleep(3.0)
                    self._try_open()
                    continue

                with self.lock:
                    waiting = self.ser.in_waiting if self.ser else 0

                if waiting > 0:
                    with self.lock:
                        raw = self.ser.readline()
                    try:
                        line = raw.decode('utf-8', errors='ignore').strip()
                        if line:
                            self._parse_line(line)
                    except Exception as parse_err:
                        print(f"[SERIAL ERROR] Parsing exception: {parse_err}")
                else:
                    time.sleep(0.05)

            except serial.SerialException as serial_err:
                print(f"[SERIAL ERROR] SerialException: {serial_err}")
                with self.lock:
                    try:
                        if self.ser:
                            self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
                self._set_hardware_online(False)
                time.sleep(3.0)

            except Exception as err:
                print(f"[SERIAL ERROR] Unexpected error in read loop: {err}")
                time.sleep(1.0)

    def _parse_line(self, line):
        """Parse a single line from the ESP32.  Format: EVENT_NAME:DATA or EVENT_NAME
        Debug lines (starting with '[') from DEBUG_PRINTLN are ignored."""
        # Skip debug/log lines from the firmware's DEBUG_PRINTLN macro
        if line.startswith("["):
            return

        parts = line.split(":", 1)
        event_name = parts[0].strip()
        data = parts[1].strip() if len(parts) > 1 else ""

        # Only process non-empty event names
        if not event_name:
            return

        print(f"[SERIAL IN] {event_name} -> {data}")

        if self.event_callback:
            self.event_callback(event_name, data)
