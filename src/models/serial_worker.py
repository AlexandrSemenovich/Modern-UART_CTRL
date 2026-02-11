"""
SerialWorker: QThread-based worker for handling serial port communication.
Provides line-buffered reading, write queueing, and signal-based event emission.

Refactored with:
- Full type hints
- Improved error handling with logging
- Configurable timing
- Better exception hierarchy
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal, QThread
from typing import Optional, Dict, Any
import logging
import queue
import time
import traceback

from src.utils.translator import tr

# Try to import pyserial, provide fallback
try:
    import serial
    from serial import SerialException
    HAS_PYSERIAL = True
except ImportError:
    serial = None  # type: ignore
    SerialException = Exception  # type: ignore
    HAS_PYSERIAL = False


logger = logging.getLogger(__name__)


class SerialWorker(QThread):
    """
    Worker for a single serial port running in its own QThread.
    
    Features:
    - Line buffering: Only emits complete lines (ending with \\r\\n, \\n, or \\r)
    - Write queueing: Thread-safe write queue
    - Signal-based events: rx, status, error signals for UI binding
    - Comprehensive error handling with logging
    
    Signals:
        rx (str, str): (port_label, data) - received data (complete line)
        status (str, str): (port_label, status_message) - status updates
        error (str, str): (port_label, error_message) - error messages
        finished (): Worker has finished execution
    """
    
    # Signals
    rx = Signal(str, str)         # port_label, data
    status = Signal(str, str)     # port_label, message
    error = Signal(str, str)       # port_label, error_message
    finished = Signal()            # Worker finished
    
    # Configuration defaults
    DEFAULT_TIMEOUT: float = 0.1   # seconds
    READ_INTERVAL: float = 0.02   # seconds (20ms)
    DEFAULT_BAUD: int = 115200
    
    # Max consecutive errors before giving up
    MAX_CONSECUTIVE_ERRORS = 3
    
    def __init__(self, port_label: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SerialWorker.
        
        Args:
            port_label (str): Logical label for this port (e.g., 'CPU1', 'CPU2', 'TLM')
            config (Optional[Dict]): Configuration dictionary with optional keys:
                - 'timeout': Read timeout in seconds (default: 0.1)
                - 'read_interval': Sleep interval in seconds (default: 0.02)
        """
        super().__init__()
        
        self._port_label = port_label
        self._config = config or {}
        
        # Serial connection state
        self._port_name: Optional[str] = None
        self._baud: int = self.DEFAULT_BAUD
        self._timeout: float = self._config.get('timeout', self.DEFAULT_TIMEOUT)
        self._read_interval: float = self._config.get('read_interval', self.READ_INTERVAL)
        
        # Thread control
        self._running: bool = False
        self._write_q: queue.Queue = queue.Queue()
        
        # Buffer for incomplete lines
        self._read_buffer: str = ""
        
        # Serial port instance
        self._ser: Optional[Any] = None
        
        # Error tracking
        self._consecutive_errors: int = 0
        self._should_stop: bool = False
    
    @property
    def port_label(self) -> str:
        """Get port label."""
        return self._port_label
    
    @property
    def port_name(self) -> Optional[str]:
        """Get configured port name."""
        return self._port_name
    
    @property
    def baud_rate(self) -> int:
        """Get configured baud rate."""
        return self._baud
    
    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running
    
    def configure(
        self, 
        port: str, 
        baud: int, 
        timeout: Optional[float] = None
    ) -> None:
        """
        Configure the serial port and baud rate.
        
        Args:
            port (str): Port name (e.g., 'COM1', '/dev/ttyUSB0')
            baud (int): Baud rate (e.g., 9600, 115200)
            timeout (Optional[float]): Read timeout in seconds
        """
        self._port_name = port
        self._baud = baud
        if timeout is not None:
            self._timeout = timeout
        
        logger.debug(f"Configured {self._port_label}: port={port}, baud={baud}, timeout={self._timeout}")
    
    def configure_from_dict(self, config: Dict[str, Any]) -> None:
        """
        Configure from dictionary.
        
        Args:
            config: Configuration dictionary with keys:
                - 'port': Port name
                - 'baud': Baud rate
                - 'timeout': Optional read timeout
                - 'data_bits': Optional data bits
                - 'parity': Optional parity
                - 'stop_bits': Optional stop bits
        """
        self._port_name = config.get('port')
        self._baud = config.get('baud', self.DEFAULT_BAUD)
        self._timeout = config.get('timeout', self.DEFAULT_TIMEOUT)
        
        logger.debug(f"Configured {self._port_label} from dict: {config}")
    
    def run(self) -> None:
        """
        Main thread loop: handles reading and writing to serial port.
        Only emits complete lines (terminated by \\r, \\n, or \\r\\n).
        """
        self._running = True
        self._should_stop = False
        self._consecutive_errors = 0
        
        self._emit_status(tr("worker_connecting_to", "Connecting to {port}...").format(
            port=self._port_name or 'N/A'
        ))
        
        ser: Optional[Any] = None
        connection_error: Optional[str] = None
        
        # Attempt to open the port
        try:
            if HAS_PYSERIAL and self._port_name:
                try:
                    # Create serial instance with configurable timeout
                    ser = serial.Serial(
                        self._port_name,
                        self._baud,
                        timeout=self._timeout
                    )
                    
                    # Additional configuration if provided
                    if 'data_bits' in self._config:
                        ser.bytesize = self._config['data_bits']
                    if 'parity' in self._config:
                        ser.parity = self._config['parity']
                    if 'stop_bits' in self._config:
                        ser.stopbits = self._config['stop_bits']
                    
                    # Ensure port is actually open
                    if not getattr(ser, 'is_open', True):
                        ser.open()
                    
                    self._ser = ser
                    
                    self._emit_status(tr("worker_connected_to", "Connected to {port}").format(
                        port=self._port_name
                    ))
                    
                    logger.info(f"Successfully connected to {self._port_name}")
                    
                except SerialException as e:
                    connection_error = str(e)
                    logger.error(f"Serial connection error: {e}")
                    self._emit_error(tr("worker_open_error", "Open error ({port}): {error}").format(
                        port=self._port_name or 'N/A',
                        error=e
                    ))
                    self._running = False
                    self._cleanup(ser)
                    self.finished.emit()
                    return
            else:
                # No pyserial - simulation mode
                logger.warning("pyserial not available, running in simulation mode")
                self._ser = None
                self._emit_status(tr("worker_simulated", "Simulation mode (no pyserial)"))
        
        except Exception as e:
            connection_error = str(e)
            logger.exception(f"Unexpected error during connection: {e}")
            self._emit_error(tr("worker_open_error", "Connection error: {error}").format(error=e))
            self._running = False
            self._cleanup(ser)
            self.finished.emit()
            return
        
        # Main loop
        try:
            while self._running and not self._should_stop:
                try:
                    read_ok = self._process_read(ser)
                    
                    # Track errors
                    if not read_ok:
                        self._consecutive_errors += 1
                        if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                            logger.error(f"Too many consecutive errors, stopping {self._port_label}")
                            self._emit_error(tr("worker_too_many_errors", "Too many errors, disconnecting"))
                            break
                    else:
                        self._consecutive_errors = 0
                
                except SerialException as e:
                    # Handle permission errors gracefully
                    logger.warning(f"Serial exception on {self._port_label}: {e}")
                    self._emit_error(str(e))
                    self._consecutive_errors += 1
                    if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        break
                
                except Exception as e:
                    logger.exception(f"Unexpected error in read loop: {e}")
                    self._emit_error(str(e))
                    self._consecutive_errors += 1
                    if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        break
                
                self._process_write()
                
                # Keep UI responsive with configurable interval
                time.sleep(self._read_interval)
        
        except Exception as e:
            logger.exception(f"Fatal error in worker loop: {e}")
            self._emit_error(tr("worker_fatal_error", "Fatal error: {error}").format(error=e))
        
        finally:
            self._cleanup(ser)
            self.finished.emit()
    
    def _cleanup(self, ser: Optional[Any]) -> None:
        """Cleanup resources."""
        self._running = False
        self._should_stop = True
        
        # Close serial port
        try:
            if ser is not None and getattr(ser, 'is_open', False):
                ser.close()
                logger.debug(f"Closed serial port {self._port_name}")
        except Exception as e:
            logger.warning(f"Error closing port: {e}")
        
        self._emit_status(tr("worker_disconnected_from", "Disconnected from {port}").format(
            port=self._port_name or 'N/A'
        ))
    
    def _process_read(self, ser: Optional[Any]) -> bool:
        """
        Process incoming data from serial port.
        
        Returns:
            True if successful, False on error
        """
        if ser is None:
            return True
        
        try:
            # Check if data is available
            if hasattr(ser, 'in_waiting') and ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                
                if data:
                    try:
                        text = data.decode('utf-8', errors='replace')
                    except Exception:
                        # Fallback to repr if decode fails
                        text = repr(data)
                    
                    # Buffer data and emit only complete lines
                    self._read_buffer += text
                    self._emit_complete_lines()
            
            return True
        
        except SerialException as e:
            # Permission errors are common when port is being closed
            if "PermissionError" in str(e) or "Access" in str(e):
                logger.warning(f"Permission error reading from {self._port_label}: {e}")
                return False
            raise
        
        except Exception as e:
            logger.warning(f"Error reading from serial: {e}")
            return False
    
    def _emit_complete_lines(self) -> None:
        """Process read buffer and emit complete lines."""
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
            buffer_len = len(self._read_buffer)
            
            # Safety check
            if first_idx >= buffer_len:
                break
            
            # Extract line
            line = self._read_buffer[:first_idx]
            
            # Determine which line ending was used and skip it
            if first_idx + 2 <= buffer_len and self._read_buffer[first_idx:first_idx+2] == '\r\n':
                self._read_buffer = self._read_buffer[first_idx+2:]
            else:
                self._read_buffer = self._read_buffer[first_idx+1:]
            
            # Emit complete line with line ending
            self.rx.emit(self._port_label, line + '\n')
    
    def _process_write(self) -> None:
        """Process outgoing write queue."""
        items = []
        try:
            while True:
                items.append(self._write_q.get_nowait())
        except queue.Empty:
            pass
        for item in items:
            self._send_data(item)
    
    def _send_data(self, data: str) -> bool:
        """
        Send data through serial port.
        
        Args:
            data: Data to send
            
        Returns:
            True if successful
        """
        try:
            if self._ser is not None:
                # Add CR+LF to the outgoing data if not present
                data_to_send = data if data.endswith('\r\n') else data + '\r\n'
                
                try:
                    bytes_written = self._ser.write(data_to_send.encode())
                    logger.debug(f"TX to {self._port_label}: {bytes_written} bytes")
                except SerialException as e:
                    raise
                
                self._emit_status(tr("worker_tx_message", "TX: {data}").format(data=data))
                
                # Echo for simulation mode
                if self._ser is None:
                    self.rx.emit(self._port_label, tr(
                        "worker_simulated_echo", 
                        "(simulated echo) {data}"
                    ).format(data=data))
                
                return True
            else:
                # Not connected
                raise RuntimeError("Port not open")
        
        except Exception as e:
            logger.exception(f"Write error on {self._port_label}: {e}")
            self._emit_error(tr("worker_write_error", "Write error ({port}): {error}").format(
                port=self._port_name or 'N/A',
                error=e
            ))
            return False
    
    def _emit_status(self, message: str) -> None:
        """Emit status signal."""
        self.status.emit(self._port_label, message)
    
    def _emit_error(self, message: str) -> None:
        """Emit error signal."""
        self.error.emit(self._port_label, message)
    
    def write(self, data: str) -> bool:
        """
        Queue a string to be written to the serial port.
        Will be sent with CR+LF appended if not already present.
        
        Args:
            data (str): Text to send to the serial port
            
        Returns:
            True if data was queued successfully
        """
        if not data:
            return False
        
        self._write_q.put(data)
        return True
    
    def write_bytes(self, data: bytes) -> bool:
        """
        Queue bytes to be written to the serial port.
        
        Args:
            data (bytes): Bytes to send
            
        Returns:
            True if data was queued successfully
        """
        if not data:
            return False
        
        try:
            self._write_q.put(data)
            return True
        except Exception:
            return False
    
    def stop(self) -> None:
        """Stop the worker thread gracefully."""
        logger.info(f"Stopping worker for {self._port_label}")
        self._should_stop = True
        self._running = False
        
        # Try to close serial immediately to unblock reads/writes
        if self._ser is not None:
            try:
                self._ser.flush()
            except Exception:
                pass
            
            try:
                self._ser.close()
            except Exception:
                pass
        
        # Wait for thread to finish gracefully
        if self.isRunning():
            self.wait(1000)
    
    def flush_queue(self) -> int:
        """
        Clear and return number of items in write queue.
        
        Returns:
            Number of items flushed
        """
        count = 0
        while not self._write_q.empty():
            try:
                self._write_q.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count
    
    def get_queue_size(self) -> int:
        """
        Get current write queue size.
        
        Returns:
            Number of items in queue
        """
        return self._write_q.qsize()
