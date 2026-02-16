"""
ComPortViewModel: ViewModel for a single COM port.
Handles all business logic for one serial port connection.
"""

from PySide6 import QtCore
from PySide6.QtCore import Signal, QObject
from typing import Optional, Dict, Any
import html
import logging
import threading
import time

from src.utils.translator import tr
from src.models.serial_worker import SerialWorker
from src.styles.constants import SerialConfig, SerialPorts, CommandConfig
from src.utils.config_loader import config_loader
from src.utils.theme_manager import theme_manager
from src.utils.port_manager import port_manager
from src.utils.state_utils import PortConnectionState

logger = logging.getLogger(__name__)


class ComPortViewModel(QObject):
    """
    ViewModel for managing a single COM port.
    
    Responsibilities:
    - Port configuration and connection management
    - Data transmission and reception
    - State management
    - Counter tracking
    
    Signals:
        state_changed (str): New connection state
        data_received (str): Received data text
        data_sent (str): Sent data text
        error_occurred (str): Error message
        counter_updated (int, int): RX and TX counts
    """
    
    # Signals for View binding
    state_changed = Signal(str)  # ConnectionState
    data_received = Signal(str)   # Formatted RX data
    data_sent = Signal(str)      # Formatted TX data
    error_occurred = Signal(str) # Error message
    counter_updated = Signal(int, int)  # rx_count, tx_count
    
    def __init__(
        self, 
        port_label: str,
        port_number: int,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ComPortViewModel.
        
        Args:
            port_label: Display label (e.g., "CPU1", "CPU2", "TLM")
            port_number: Port number (1-based index)
            config: Optional configuration dictionary
        """
        super().__init__()
        
        self._port_label = port_label
        self._port_number = port_number
        self._config = config or {}
        
        # Connection state
        self._state = PortConnectionState.DISCONNECTED
        self._port_name: Optional[str] = None
        self._baud_rate: int = self._config.get('default_baud_rate', 115200)
        
        # Counters
        self._rx_count: int = 0
        self._tx_count: int = 0
        
        # Extended metrics for monitoring
        self._rx_bytes: int = 0
        self._tx_bytes: int = 0
        self._error_count: int = 0
        self._connection_time: float = 0.0  # Unix timestamp when connected
        self._last_rx_time: float = 0.0  # For throughput calculation
        self._last_tx_time: float = 0.0
        
        # Serial worker
        self._worker: Optional[SerialWorker] = None
        
        # Available ports cache
        self._available_ports: list = []
        
        # Theme colors - load from config
        self._colors = config_loader.get_colors(self._current_theme())
        theme_manager.theme_changed.connect(self._on_theme_changed)
    
    @property
    def port_label(self) -> str:
        """Get port display label."""
        return self._port_label
    
    @property
    def port_number(self) -> int:
        """Get port number (1-based)."""
        return self._port_number
    
    @property
    def state(self) -> PortConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def port_name(self) -> Optional[str]:
        """Get selected port name."""
        return self._port_name
    
    @property
    def baud_rate(self) -> int:
        """Get current baud rate."""
        return self._baud_rate
    
    @property
    def rx_count(self) -> int:
        """Get RX counter value."""
        return self._rx_count
    
    @property
    def tx_count(self) -> int:
        """Get TX counter value."""
        return self._tx_count
    
    @property
    def error_count(self) -> int:
        """Get error counter value."""
        return self._error_count
    
    @property
    def connection_time(self) -> float:
        """Get connection duration in seconds."""
        if self._connection_time > 0:
            return time.time() - self._connection_time
        return 0.0
    
    @property
    def is_connected(self) -> bool:
        """Check if port is connected."""
        return self._state == PortConnectionState.CONNECTED
    
    @property
    def available_ports(self) -> list:
        """Get list of available COM ports."""
        return self._available_ports.copy()
    
    def _current_theme(self) -> str:
        """Get current theme name."""
        return "light" if theme_manager.is_light_theme() else "dark"
    
    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change event."""
        self._colors = config_loader.get_colors(theme)
    
    def set_port_name(self, port_name: str) -> None:
        """Set the COM port name to connect to."""
        self._port_name = port_name

    def set_port_label(self, label: str) -> None:
        """Update display label (used for UI when language changes)."""
        self._port_label = label

    def set_baud_rate(self, baud_rate: int) -> None:
        """
        Set baud rate for connection.
        
        Args:
            baud_rate: Valid baud rate from SerialConfig.BAUD_RATES
        """
        if baud_rate in SerialConfig.BAUD_RATES:
            self._baud_rate = baud_rate
        else:
            logger.warning(f"Invalid baud rate {baud_rate}, using {self._baud_rate}")
    
    def set_available_ports(self, ports: list) -> None:
        """Update list of available COM ports."""
        self._available_ports = ports
        logger.debug(f"Available ports updated: {ports}")
    
    def connect(self) -> bool:
        """
        Establish connection to the configured serial port.
        
        Returns:
            True if connection initiated successfully, False otherwise
        """
        if self._state == PortConnectionState.CONNECTED:
            logger.warning(f"Port {self._port_label} already connected")
            return False
        
        if not self._port_name:
            self._emit_error(tr("error_no_port", "No port selected"))
            return False

        if self._port_name.upper() in SerialPorts.SYSTEM_PORTS:
            self._emit_error(tr("error_system_port", "System COM ports cannot be used"))
            return False

        # Check if port is already in use (atomic operation)
        if not port_manager.acquire(self._port_name):
            self._emit_error(tr("error_port_in_use", "Port already in use"))
            return False

        self._set_state(PortConnectionState.CONNECTING)

        # Create worker running in its own QThread
        self._worker = SerialWorker(self._port_label)
        self._worker.configure(self._port_name, self._baud_rate)

        # Connect signals directly to the worker thread
        self._worker.rx.connect(self._on_data_received)
        self._worker.error.connect(self._on_error_occurred)
        self._worker.status.connect(self._on_status_changed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._worker.deleteLater)

        # Start worker thread
        self._worker.start()
        
        logger.info(f"Connecting to {self._port_name} at {self._baud_rate} baud")
        return True
    
    def connect_with_retry(self, max_attempts: int = 3, initial_backoff_ms: int = 500) -> bool:
        """
        Establish connection to the configured serial port with retry and exponential backoff.
        
        Args:
            max_attempts: Maximum number of connection attempts
            initial_backoff_ms: Initial backoff time in milliseconds
            
        Returns:
            True if connection initiated successfully, False otherwise
        """
        if self._state == PortConnectionState.CONNECTED:
            logger.warning(f"Port {self._port_label} already connected")
            return False
        
        if not self._port_name:
            self._emit_error(tr("error_no_port", "No port selected"))
            return False
        
        if self._port_name.upper() in SerialPorts.SYSTEM_PORTS:
            self._emit_error(tr("error_system_port", "System COM ports cannot be used"))
            return False
        
        # Check if port is already in use (atomic operation)
        if not port_manager.acquire(self._port_name):
            self._emit_error(tr("error_port_in_use", "Port already in use"))
            return False
        
        # Attempt connection with retry
        from PySide6.QtCore import QTimer
        
        def attempt_connection(attempt: int, backoff_ms: int) -> bool:
            if attempt >= max_attempts:
                self._emit_error(tr("error_connection_failed", "Connection failed after {attempts} attempts").format(attempts=max_attempts))
                self._set_state(PortConnectionState.ERROR)
                return False
            
            self._set_state(PortConnectionState.CONNECTING)
            
            # Create worker running in its own QThread
            self._worker = SerialWorker(self._port_label)
            self._worker.configure(self._port_name, self._baud_rate)
            
            # Connect signals directly to the worker thread
            self._worker.rx.connect(self._on_data_received)
            self._worker.error.connect(lambda msg: self._on_retry_error(msg, attempt + 1, backoff_ms * 2))
            self._worker.status.connect(self._on_status_changed)
            self._worker.finished.connect(self._on_worker_finished)
            self._worker.finished.connect(self._worker.deleteLater)
            
            # Start worker thread
            self._worker.start()
            
            logger.info(f"Connecting to {self._port_name} at {self._baud_rate} baud (attempt {attempt + 1}/{max_attempts})")
            return True
        
        # Start first connection attempt
        return attempt_connection(1, initial_backoff_ms)
    
    def _on_retry_error(self, port_label: str, error_message: str, next_attempt: int) -> None:
        """Handle error with retry suggestion."""
        if self._state == PortConnectionState.CONNECTING:
            logger.warning(f"Connection error on attempt {next_attempt}: {error_message}")
            # Connection will be cleaned up by _on_worker_finished
    
    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        if self._state == PortConnectionState.DISCONNECTED:
            return

        self._safe_stop_worker()

        # Release port from active ports
        port_manager.release(self._port_name)

        self._set_state(PortConnectionState.DISCONNECTED)
        logger.info(f"Disconnected from {self._port_label}")
    
    def send_data(self, data: str) -> bool:
        """
        Send data through the serial port.
        
        Args:
            data: Text data to send
            
        Returns:
            True if data was queued successfully
        """
        if not self._worker or self._state != PortConnectionState.CONNECTED:
            self._emit_error(tr("error_not_connected", "Port not connected"))
            return False
        
        # Validate command length
        if len(data) > CommandConfig.MAX_COMMAND_LENGTH:
            self._emit_error(tr("error_command_too_long", "Command too long (max {max} chars)").format(max=CommandConfig.MAX_COMMAND_LENGTH))
            return False
        
        # Validate characters (allow only printable ASCII + CR + LF)
        if not all(c in CommandConfig.VALID_CHARS for c in data):
            self._emit_error(tr("error_invalid_chars", "Invalid characters in command"))
            return False
        
        # Queue data for sending
        self._worker.write(data)
        
        # Update TX counter
        self._tx_count += 1
        self._emit_counter_update()
        
        # Emit TX data for display (View will format)
        self.data_sent.emit(data)
        
        logger.debug(f"TX to {self._port_label}: {data}")
        return True
    
    def send_command(self, command: str) -> bool:
        """
        Send a command with automatic newline.
        
        Args:
            command: Command text without newline
            
        Returns:
            True if command was sent successfully
        """
        # Add CR+LF if not present
        if not command.endswith('\r\n'):
            command = command + '\r\n'
        return self.send_data(command)
    
    def clear_counters(self) -> None:
        """Reset RX and TX counters to zero."""
        self._rx_count = 0
        self._tx_count = 0
        self._rx_bytes = 0
        self._tx_bytes = 0
        self._error_count = 0
        self._connection_time = 0.0
        self._emit_counter_update()
    
    def _set_state(self, new_state: PortConnectionState | str) -> None:
        """
        Update connection state and emit signal.
        
        Args:
            new_state: New state to set
        """
        if isinstance(new_state, str):
            normalized_state = self._normalize_state(new_state)
        else:
            normalized_state = new_state

        if self._state != normalized_state:
            old_state = self._state
            self._state = normalized_state
            logger.debug(f"State changed: {old_state} -> {normalized_state}")

            state_payload = (
                normalized_state.value
                if isinstance(normalized_state, PortConnectionState)
                else str(normalized_state)
            )
            self.state_changed.emit(state_payload)

    @staticmethod
    def _normalize_state(state: str | PortConnectionState) -> PortConnectionState:
        if isinstance(state, PortConnectionState):
            return state
        candidate = state.split('.')[-1].lower()
        for option in PortConnectionState:
            if option.value == candidate or option.name.lower() == candidate:
                return option
        return PortConnectionState.DISCONNECTED
    
    def _on_data_received(self, port_label: str, data: str) -> None:
        """
        Handle received data from serial port.
        
        Args:
            port_label: Source port label
            data: Received data text
        """
        # Update RX counter
        self._rx_count += 1
        self._emit_counter_update()
        
        # Emit RX data for display (View will format)
        self.data_received.emit(data)
        
        logger.debug(f"RX from {port_label}: {data}")
    
    def _on_error_occurred(self, port_label: str, error_message: str) -> None:
        """
        Handle error from serial worker.
        
        Args:
            port_label: Source port label
            error_message: Error description
        """
        logger.error(f"Error on {port_label}: {error_message}")
        
        # Increment error counter
        self._error_count += 1
        self._emit_counter_update()
        
        # Surface error to UI and mark the port as faulted
        self._set_state(PortConnectionState.ERROR)
        self._emit_error(error_message)

        # Ensure worker is stopped
        self._safe_stop_worker()
    
    def _on_status_changed(self, port_label: str, status_message: str) -> None:
        """
        Handle status update from serial worker.

        Args:
            port_label: Source port label
            status_message: Status text
        """
        port_name = self._port_name or "N/A"

        connected_msg = tr("worker_connected_to", "Connected to {port}").format(port=port_name)
        disconnected_msg = tr("worker_disconnected_from", "Disconnected from {port}").format(port=port_name)
        connecting_msg = tr("worker_connecting_to", "Connecting to {port}...").format(port=port_name)

        if status_message == connected_msg:
            self._set_state(PortConnectionState.CONNECTED)
            # Track connection time
            self._connection_time = time.time()
        elif status_message == disconnected_msg:
            self._set_state(PortConnectionState.DISCONNECTED)
        elif status_message == connecting_msg:
            self._set_state(PortConnectionState.CONNECTING)

        logger.debug(f"Status {port_label}: {status_message}")
    
    def _format_rx_data(self, data: str) -> str:
        """
        Format received data for display.
        
        Args:
            data: Raw received data
            
        Returns:
            HTML formatted string for display
        """
        from PySide6.QtCore import QDateTime
        
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        escaped_data = html.escape(data.rstrip('\r\n'))
        
        return (
            f"<span style='color:gray'>[{timestamp}]</span> "
            f"<b style='color:{self._colors.rx_label}'>RX({self._port_label}):</b> "
            f"<span style='color:{self._colors.rx_text}; white-space:pre'>{escaped_data}</span><br>"
        )
    
    def _format_tx_data(self, data: str) -> str:
        """
        Format sent data for display.
        
        Args:
            data: Raw sent data
            
        Returns:
            HTML formatted string for display
        """
        from PySide6.QtCore import QDateTime
        
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        escaped_data = html.escape(data.rstrip('\r\n'))
        
        return (
            f"<span style='color:gray'>[{timestamp}]</span> "
            f"<b style='color:{self._colors.tx_label}'>TX({self._port_label}):</b> "
            f"<span style='color:{self._colors.tx_text}; white-space:pre'>{escaped_data}</span><br>"
        )
    
    def _emit_error(self, message: str) -> None:
        """Emit error signal with formatted message."""
        from PySide6.QtCore import QDateTime
        
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss')
        # Use plain text with html.escape for safety
        escaped_message = html.escape(message)
        formatted = (
            f"<span class=\"timestamp\">[{timestamp}]</span> "
            f"<span class=\"error\">ERROR:</span> {escaped_message}<br>"
        )
        self.error_occurred.emit(formatted)
    
    def _emit_counter_update(self) -> None:
        """Emit counter update signal."""
        self.counter_updated.emit(self._rx_count, self._tx_count)
    
    def shutdown(self) -> None:
        """Clean shutdown of the port and worker."""
        self._safe_stop_worker()
        
        # Release port from active ports
        port_manager.release(self._port_name)

        self._set_state(PortConnectionState.DISCONNECTED)
        logger.info(f"Shutdown complete for {self._port_label}")

    def _on_worker_finished(self) -> None:
        # Release port from active ports
        port_manager.release(self._port_name)
        self._worker = None
        # Return to disconnected state if we were connecting
        if self._state == PortConnectionState.CONNECTING:
            self._set_state(PortConnectionState.DISCONNECTED)

    def _safe_stop_worker(self) -> None:
        if self._worker:
            try:
                self._worker.stop()
                if self._worker.isRunning():
                    self._worker.wait(1000)
            except RuntimeError:
                pass
