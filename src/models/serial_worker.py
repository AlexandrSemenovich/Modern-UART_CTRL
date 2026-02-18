"""
SerialWorker: QThread-based worker for handling serial port communication.
Provides line-buffered reading, write queueing, and signal-based event emission.

Refactored with:
- Full type hints
- Improved error handling with logging
- Configurable timing
- Better exception hierarchy
- Connection timeout support
- Production logging levels
- Charset detection options
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal, QThread
from typing import Optional, Dict, Any
import logging
import queue
import time
import traceback
import os
from enum import Enum

from src.utils.translator import tr
from src.utils.config_loader import config_loader
from src.styles.constants import CharsetConfig
from src.utils.profiler import PerformanceTimer

# Enable/disable profiling via environment variable
_ENABLE_PROFILING = os.environ.get('APP_PROFILE', '').lower() == 'true'

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

# Logging levels for production vs development
class LoggingLevel(Enum):
    """Logging level configuration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

# Default production logging level (WARNING to reduce noise)
_DEFAULT_LOGGING_LEVEL = LoggingLevel.WARNING


def _get_effective_logging_level() -> int:
    """Get the effective logging level based on environment."""
    import os
    env_level = os.environ.get('SERIAL_WORKER_LOG_LEVEL')
    if env_level:
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
        }
        return level_map.get(env_level.upper(), _DEFAULT_LOGGING_LEVEL.value)
    return _DEFAULT_LOGGING_LEVEL.value


# Set default logging level for this module
logging.addLevelName(logging.DEBUG, 'DEBUG')
logging.addLevelName(logging.INFO, 'INFO')
logging.addLevelName(logging.WARNING, 'WARNING')
logging.addLevelName(logging.ERROR, 'ERROR')

# Apply default logging level
logger.setLevel(_get_effective_logging_level())


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
    
    # Configuration defaults - load from config
    _timing_config = config_loader.get_serial_timing()
    DEFAULT_TIMEOUT: float = 0.1   # seconds
    READ_INTERVAL: float = _timing_config["default_read_interval"]   # seconds
    DEFAULT_BAUD: int = 115200
    
    # Connection timeout (5 seconds)
    CONNECTION_TIMEOUT: float = _timing_config["connection_timeout"]  # seconds
    
    # Connection retry settings
    MAX_CONNECTION_ATTEMPTS = _timing_config["max_connection_attempts"]
    CONNECTION_RETRY_DELAY = _timing_config["connection_retry_delay"]  # seconds between retries
    
    # Charset detection settings
    CHARSET_AUTO_DETECT = True
    CHARSET_DETECTION_LENGTH = 1024  # bytes to sample for auto-detection
    
    # Max consecutive errors before giving up
    MAX_CONSECUTIVE_ERRORS = _timing_config["max_consecutive_errors"]
    
    # Max buffer size for incoming data (64KB) - security hardending
    MAX_BUFFER_SIZE = 65536
    
    # Rate limiting: max bytes per second (1MB/s) - DoS protection
    MAX_BYTES_PER_SECOND = 1024 * 1024
    
    # TX rate limiting: max bytes per second (256KB/s)
    MAX_TX_BYTES_PER_SECOND = 256 * 1024
    
    # Max write size (64KB) - security hardening
    MAX_WRITE_SIZE = 65536
    
    # Max write batch size - prevent queue starvation
    MAX_WRITE_BATCH = 100
    
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
        
        # Charset configuration for serial data decoding
        self._charset: str = self._config.get('charset', 'utf-8')
        self._charset_errors: str = self._config.get('charset_errors', 'replace')  # 'replace', 'ignore', 'strict'
        self._charset_auto_detect: bool = self._config.get('charset_auto_detect', False)
        self._detected_charset: Optional[str] = None
        
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
        
        # Rate limiting: track bytes received per second
        self._bytes_received: int = 0
        self._last_rate_check: float = 0.0
        
        # TX rate limiting: track bytes sent per second
        self._bytes_sent: int = 0
        self._last_tx_rate_check: float = 0.0
        
        # Connection timeout tracking
        self._connection_start_time: float = 0.0
        self._connection_timeout_reached: bool = False
        self._connection_attempts: int = 0
        
        # Logging level override
        self._log_level: Optional[int] = self._config.get('log_level')
        if self._log_level:
            logger.setLevel(self._log_level)
    
    @property
    def charset(self) -> str:
        """Get configured charset."""
        return self._charset
    
    @property
    def detected_charset(self) -> Optional[str]:
        """Get auto-detected charset if available."""
        return self._detected_charset
    
    @property
    def is_charset_auto_detect(self) -> bool:
        """Check if charset auto-detection is enabled."""
        return self._charset_auto_detect
    
    @property
    def connection_attempts(self) -> int:
        """Get number of connection attempts made."""
        return self._connection_attempts
    
    @property
    def is_connected(self) -> bool:
        """Check if serial port is currently connected."""
        return self._ser is not None and getattr(self._ser, 'is_open', False)
    
    def configure(
        self, 
        port: str, 
        baud: int, 
        timeout: Optional[float] = None,
        charset: Optional[str] = None,
        charset_auto_detect: bool = False
    ) -> None:
        """
        Configure the serial port and baud rate.
        
        Args:
            port (str): Port name (e.g., 'COM1', '/dev/ttyUSB0')
            baud (int): Baud rate (e.g., 9600, 115200)
            timeout (Optional[float]): Read timeout in seconds
            charset (Optional[str]): Character encoding for data
            charset_auto_detect (bool): Enable automatic charset detection
        """
        self._port_name = port
        self._baud = baud
        if timeout is not None:
            self._timeout = timeout
        if charset is not None:
            self._charset = charset
        self._charset_auto_detect = charset_auto_detect
        
        logger.info(f"Configured {self._port_label}: port={port}, baud={baud}, timeout={self._timeout}, charset={charset}")
    
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
                - 'charset': Character encoding
                - 'charset_auto_detect': Enable auto-detection
                - 'charset_errors': Error handling ('replace', 'ignore', 'strict')
                - 'log_level': Logging level override
        """
        self._port_name = config.get('port')
        self._baud = config.get('baud', self.DEFAULT_BAUD)
        self._timeout = config.get('timeout', self.DEFAULT_TIMEOUT)
        self._charset = config.get('charset', self._charset)
        self._charset_auto_detect = config.get('charset_auto_detect', self._charset_auto_detect)
        self._charset_errors = config.get('charset_errors', self._charset_errors)
        
        # Set logging level if provided
        log_level = config.get('log_level')
        if log_level:
            logger.setLevel(log_level)
        
        logger.info(f"Configured {self._port_label} from dict: port={self._port_name}, baud={self._baud}, charset={self._charset}")
    
    def _detect_charset(self, data: bytes) -> Optional[str]:
        """
        Attempt to detect charset from raw data bytes.
        
        Args:
            data: Raw bytes to analyze
            
        Returns:
            Detected charset name or None if detection fails
        """
        # Check for BOM patterns first
        for pattern, charset in CharsetConfig.CHARSET_PATTERNS.items():
            if data.startswith(pattern):
                logger.debug(f"Detected charset '{charset}' from BOM pattern")
                return charset
        
        # Try to decode with common charsets to find best match
        sample = data[:self.CHARSET_DETECTION_LENGTH]
        for charset in CharsetConfig.COMMON_CHARSETS:
            try:
                sample.decode(charset, errors='strict')
                # This charset works, but prefer UTF-8 if valid
                if charset == 'utf-8':
                    return charset
            except UnicodeDecodeError:
                continue
        
        # Default to latin-1 if no specific charset detected (handles most serial data)
        return 'latin-1'
    
    def _open_connection(self) -> Optional[Any]:
        """
        Open serial connection with proper error handling and timeout.
        
        Returns:
            Serial port instance or None if failed
        """
        if not HAS_PYSERIAL or not self._port_name:
            logger.warning("pyserial not available, running in simulation mode")
            self._emit_status(tr("worker_simulated", "Simulation mode (no pyserial)"))
            return None
        
        try:
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
            
            logger.info(f"Successfully connected to {self._port_name}")
            return ser
        
        except SerialException as e:
            self._connection_attempts += 1
            logger.error(f"Serial connection error (attempt {self._connection_attempts}): {e}")
            self._emit_error(tr("worker_open_error", f"Open error ({{port_name}}): {{error}}", port_name=self._port_name or "N/A", error=e))
            return None
        
        except Exception as e:
            self._connection_attempts += 1
            logger.exception(f"Unexpected error during connection (attempt {self._connection_attempts}): {e}")
            self._emit_error(tr("worker_open_error", f"Connection error: {{error}}", error=e))
            return None
    
    def _handle_read_error(self, error: Exception) -> bool:
        """
        Handle read errors with proper logging and error tracking.
        
        Returns:
            True if should continue, False if too many errors
        """
        if isinstance(error, SerialException):
            # Handle permission errors gracefully
            logger.warning(f"Serial exception on {self._port_label}: {error}")
            self._emit_error(str(error))
        else:
            logger.warning(f"Unexpected error in read loop: {error}")
            self._emit_error(str(error))
        
        self._consecutive_errors += 1
        if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
            logger.error(f"Too many consecutive errors, stopping {self._port_label}")
            self._emit_error(tr("worker_too_many_errors", "Too many errors, disconnecting"))
            return False
        return True
    
    def run(self) -> None:
        """
        Main thread loop: handles reading and writing to serial port.
        Only emits complete lines (terminated by \\r, \\n, or \\r\\n).
        """
        self._running = True
        self._should_stop = False
        self._consecutive_errors = 0
        self._bytes_received = 0
        self._last_rate_check = time.monotonic()
        self._bytes_sent = 0
        self._last_tx_rate_check = time.monotonic()
        
        self._emit_status(tr("worker_connecting_to", f"Connecting to {{port_name}}...", port_name=self._port_name or "N/A"))
        
        # Record connection start time for timeout tracking
        self._connection_start_time = time.monotonic()
        self._connection_timeout_reached = False
        
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
                    
                    self._emit_status(tr("worker_connected_to", f"Connected to {{port_name}}", port_name=self._port_name))
                    
                    logger.info(f"Successfully connected to {self._port_name}")
                    
                except SerialException as e:
                    connection_error = str(e)
                    logger.error(f"Serial connection error: {e}")
                    self._emit_error(tr("worker_open_error", f"Open error ({{port_name}}): {{error}}", port_name=self._port_name or "N/A", error=e))
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
            self._emit_error(tr("worker_open_error", f"Connection error: {{error}}", error=e))
            self._running = False
            self._cleanup(ser)
            self.finished.emit()
            return
        
        # Main loop with simplified exception handling using helper method
        try:
            while self._running and not self._should_stop:
                # Check connection timeout during initial connection
                if not self._connection_timeout_reached and self._ser is None:
                    elapsed = time.monotonic() - self._connection_start_time
                    if elapsed > self.CONNECTION_TIMEOUT:
                        logger.warning(f"Connection timeout for {self._port_label}")
                        self._emit_error(tr("worker_connection_timeout", "Connection timeout"))
                        self._connection_timeout_reached = True
                        self._running = False
                        break
                
                try:
                    read_ok = self._process_read(ser)
                    
                    # Track errors
                    if not read_ok:
                        self._consecutive_errors += 1
                        if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                            logger.error(f"Too many consecutive errors, stopping {self._port_label}")
                            self._emit_error(tr("worker_too_many_errors", "Too many errors, disconnecting"))
                            break
                        self._consecutive_errors = 0
                
                except Exception as e:
                    # Use helper method for consistent error handling
                    if not self._handle_read_error(e):
                        break
                
                self._process_write()
                
                # Keep UI responsive with Qt-native sleep
                self.msleep(int(self._read_interval * 1000))
        
        except Exception as e:
            logger.exception(f"Fatal error in worker loop: {e}")
            self._emit_error(tr("worker_fatal_error", f"Fatal error: {{error}}", error=e))
        
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
        
        self._emit_status(tr("worker_disconnected_from", f"Disconnected from {{port_name}}", port_name=self._port_name or "N/A"))
    
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
                    # Security: validate buffer size to prevent overflow
                    if len(data) > self.MAX_BUFFER_SIZE:
                        logger.warning(f"Received data exceeds MAX_BUFFER_SIZE ({len(data)} > {self.MAX_BUFFER_SIZE})")
                        data = data[:self.MAX_BUFFER_SIZE]
                    
                    # Rate limiting: track bytes received
                    self._bytes_received += len(data)
                    current_time = time.monotonic()
                    elapsed = current_time - self._last_rate_check
                    
                    # Reset rate tracking every second
                    if elapsed >= 1.0:
                        if self._bytes_received > self.MAX_BYTES_PER_SECOND:
                            logger.warning(f"Rate limit exceeded: {self._bytes_received} bytes/sec (limit: {self.MAX_BYTES_PER_SECOND})")
                        self._bytes_received = 0
                        self._last_rate_check = current_time
                    
                    # Auto-detect charset if enabled and not yet detected
                    if self._charset_auto_detect and self._detected_charset is None:
                        detected = self._detect_charset(data)
                        if detected:
                            self._detected_charset = detected
                            self._charset = detected
                            logger.info(f"Auto-detected charset: {detected}")
                    
                    try:
                        text = data.decode(self._charset, errors=self._charset_errors)
                    except Exception as e:
                        logger.debug(f"Decode error with charset {self._charset}: {e}")
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
        """
        Process outgoing write queue with batch limiting.
        Prevents queue starvation by limiting items processed per cycle.
        """
        items = []
        try:
            # Limit items per cycle to prevent starvation
            for _ in range(self.MAX_WRITE_BATCH):
                try:
                    items.append(self._write_q.get_nowait())
                except queue.Empty:
                    break
        except queue.Empty:
            pass
        for item in items:
            self._send_data(item)
    
    def _send_data(self, data) -> bool:
        """
        Send data through serial port.
        
        Args:
            data: Data to send
            
        Returns:
            True if successful
        """
        try:
            if self._ser is not None:
                # Determine if we are working with string or bytes
                is_bytes = isinstance(data, (bytes, bytearray))

                if is_bytes:
                    payload_bytes = bytes(data)
                    sanitized_for_status = repr(payload_bytes)
                else:
                    # Normalize trailing end-of-line characters added by callers
                    sanitized_data = str(data).rstrip('\r\n')

                    if not sanitized_data:
                        logger.warning(f"Rejected empty data for {self._port_label} after trimming line endings")
                        self._emit_error(tr("worker_invalid_data", "Invalid data: empty payload"))
                        return False

                    # Security: Validate data to prevent CRLF injection within payload
                    if '\n' in sanitized_data or '\r' in sanitized_data:
                        logger.warning(f"Rejected data with embedded newlines for {self._port_label}")
                        self._emit_error(tr("worker_invalid_data", "Invalid data: newlines not allowed"))
                        return False

                    # Add CR+LF to the outgoing data once sanitized
                    data_to_send = sanitized_data + '\r\n'
                    payload_bytes = data_to_send.encode()
                    sanitized_for_status = sanitized_data

                # TX rate limiting check
                current_time = time.monotonic()
                elapsed = current_time - self._last_tx_rate_check
                
                # Reset TX rate tracking every second
                if elapsed >= 1.0:
                    if self._bytes_sent > self.MAX_TX_BYTES_PER_SECOND:
                        logger.warning(f"TX rate limit exceeded: {self._bytes_sent} bytes/sec (limit: {self.MAX_TX_BYTES_PER_SECOND})")
                    self._bytes_sent = 0
                    self._last_tx_rate_check = current_time
                
                data_bytes = len(payload_bytes)
                
                # Check if adding this data would exceed rate limit
                if self._bytes_sent + data_bytes > self.MAX_TX_BYTES_PER_SECOND:
                    logger.warning(f"TX rate limit would be exceeded, queuing for next interval")
                    # Re-queue the data for later
                    return False
                
                self._bytes_sent += data_bytes
                
                try:
                    bytes_written = self._ser.write(payload_bytes)
                    logger.debug(f"TX to {self._port_label}: {bytes_written} bytes")
                except SerialException as e:
                    raise
                
                self._emit_status(tr("worker_tx_message", f"TX: {{data}}", data=sanitized_for_status))
                
                # Echo for simulation mode
                if self._ser is None:
                    self.rx.emit(self._port_label, tr(
                        "worker_simulated_echo", 
                        "(simulated echo) {data}"
                        "(simulated echo) {sanitized_data}"
                    ))

                return True
            else:
                # Not connected
                raise RuntimeError("Port not open")
        
        except Exception as e:
            logger.exception(f"Write error on {self._port_label}: {e}")
            self._emit_error(tr("worker_write_error", f"Write error ({{port_name}}): {{error}}", port_name=self._port_name or "N/A", error=e))
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
        
        # Security: validate input length
        if len(data) > self.MAX_WRITE_SIZE:
            logger.warning(f"Write data exceeds MAX_WRITE_SIZE ({len(data)} > {self.MAX_WRITE_SIZE})")
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
        
        # Security: validate input length
        if len(data) > self.MAX_WRITE_SIZE:
            logger.warning(f"Write bytes exceeds MAX_WRITE_SIZE ({len(data)} > {self.MAX_WRITE_SIZE})")
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
