"""
SerialWorker: QThread-based worker for handling serial port communication.
Provides line-buffered reading, write queueing, and signal-based event emission.
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal

from src.utils.translator import tr
import queue
import time

try:
    import serial
    HAS_PYSERIAL = True
except Exception:
    HAS_PYSERIAL = False


class SerialWorker(QtCore.QThread):
    """
    Worker for a single serial port running in its own QThread.
    
    Features:
    - Line buffering: Only emits complete lines (ending with \\r\\n, \\n, or \\r)
    - Write queueing: Thread-safe write queue
    - Signal-based events: rx, status, error signals for UI binding
    
    Signals:
        rx (str, str): (port_label, data) - received data (complete line)
        status (str, str): (port_label, status_message) - status updates
        error (str, str): (port_label, error_message) - error messages
    """
    
    rx = Signal(str, str)
    status = Signal(str, str)
    error = Signal(str, str)

    def __init__(self, port_label: str):
        """
        Initialize SerialWorker.
        
        Args:
            port_label (str): Logical label for this port (e.g., 'CPU1', 'CPU2', 'AUX')
        """
        super().__init__()
        self.port_label = port_label
        self._port = None
        self._baud = 9600
        self._running = False
        self._write_q = queue.Queue()
        self._lock = QtCore.QMutex()
        self._read_buffer = ""  # Buffer for incomplete lines
        self._ser = None
        self._port_name = None

    def configure(self, port: str, baud: int) -> None:
        """
        Configure the serial port and baud rate.
        
        Args:
            port (str): Port name (e.g., 'COM1', '/dev/ttyUSB0')
            baud (int): Baud rate (e.g., 9600, 115200)
        """
        self._port_name = port
        self._baud = baud

    def run(self):
        """
        Main thread loop: handles reading and writing to serial port.
        Only emits complete lines (terminated by \\r, \\n, or \\r\\n).
        """
        self._running = True
        pname = getattr(self, '_port_name', 'N/A')
        self.status.emit(
            self.port_label,
            tr("worker_connecting_to", "Connecting to {port}...").format(port=pname)
        )

        ser = None
        try:
            if HAS_PYSERIAL:
                # Attempt to open the port with guarded parameters
                ser = serial.Serial(getattr(self, '_port_name', ''), self._baud, timeout=0.1)
                # Ensure port is actually open
                if not getattr(ser, 'is_open', True):
                    ser.open()
            else:
                ser = None
            self._ser = ser
            # Emit a more descriptive status including physical port name
            pname = getattr(self, '_port_name', 'N/A')
            self.status.emit(
                self.port_label,
                tr("worker_connected_to", "Connected to {port}").format(port=pname)
            )
        except Exception as e:
            pname = getattr(self, '_port_name', 'N/A')
            self.error.emit(
                self.port_label,
                tr("worker_open_error", "Open error ({port}): {error}").format(port=pname, error=e)
            )
            self._running = False
            return

        try:
            while self._running:
                # Read incoming data
                try:
                    if ser is not None and getattr(ser, 'in_waiting', 0):
                        data = ser.read(getattr(ser, 'in_waiting', 0))
                        if data:
                            try:
                                text = data.decode(errors='replace')
                            except Exception:
                                text = repr(data)
                            
                            # Buffer data and emit only complete lines
                            self._read_buffer += text
                            
                            # Split by line endings but keep track of what we've sent
                            while True:
                                # Check for any line ending: \r\n, \n, or \r
                                idx_rn = self._read_buffer.find('\r\n')
                                idx_n = self._read_buffer.find('\n')
                                idx_r = self._read_buffer.find('\r')
                                
                                # Find the first occurring line ending
                                indices = [i for i in [idx_rn, idx_n, idx_r] if i >= 0]
                                if not indices:
                                    break  # No complete line yet
                                
                                first_idx = min(indices)
                                line = self._read_buffer[:first_idx]
                                
                                # Determine which line ending was used and skip it
                                if self._read_buffer[first_idx:first_idx+2] == '\r\n':
                                    self._read_buffer = self._read_buffer[first_idx+2:]
                                else:
                                    self._read_buffer = self._read_buffer[first_idx+1:]
                                
                                # Emit complete line with line ending preserved
                                self.rx.emit(self.port_label, line + '\n')
                    else:
                        # no serial: small sleep
                        pass
                except Exception as e:
                    self.error.emit(
                        self.port_label,
                        tr("worker_read_error", "Read error: {error}").format(error=e)
                    )

                # Handle outgoing write queue
                try:
                    item = self._write_q.get_nowait()
                except queue.Empty:
                    item = None

                if item is not None:
                    try:
                        if self._ser is not None:
                            # Add CR+LF to the outgoing data
                            data_to_send = item if item.endswith('\r\n') else item + '\r\n'
                            try:
                                self._ser.write(data_to_send.encode())
                            except Exception as we:
                                raise
                        else:
                            # Not connected
                            raise RuntimeError("Port not open")
                        self.status.emit(
                            self.port_label,
                            tr("worker_tx_message", "TX: {data}").format(data=item)
                        )
                        # Also emit rx-like echo if no real device (for debug)
                        if ser is None:
                            self.rx.emit(
                                self.port_label,
                                tr("worker_simulated_echo", "(simulated echo) {data}").format(data=item)
                            )
                    except Exception as e:
                        pname = getattr(self, '_port_name', 'N/A')
                        self.error.emit(
                            self.port_label,
                            tr("worker_write_error", "Write error ({port}): {error}").format(
                                port=pname,
                                error=e
                            )
                        )

                # Keep UI responsive with small sleep
                time.sleep(0.02)

        finally:
            try:
                if ser is not None:
                    ser.close()
            except Exception:
                pass
            pname = getattr(self, '_port_name', 'N/A')
            self.status.emit(
                self.port_label,
                tr("worker_disconnected_from", "Disconnected from {port}").format(port=pname)
            )

    def write(self, data: str) -> None:
        """
        Queue a string to be written to the serial port.
        Will be sent with CR+LF appended if not already present.
        
        Args:
            data (str): Text to send to the serial port
        """
        self._write_q.put(data)

    def stop(self) -> None:
        """Stop the worker thread gracefully."""
        self._running = False
        # Try to close serial immediately to unblock reads/writes
        try:
            if hasattr(self, '_ser') and self._ser is not None:
                try:
                    self._ser.flush()
                except Exception:
                    pass
                try:
                    self._ser.close()
                except Exception:
                    pass
        except Exception:
            pass

        # Wait for thread to finish gracefully
        self.wait(1000)
