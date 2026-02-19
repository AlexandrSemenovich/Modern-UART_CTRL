"""
Protocol definitions for ViewModels.
Provides abstract interfaces for type-safe dependency injection.
"""

from typing import Protocol, Optional, runtime_checkable, Any

from src.utils.state_utils import PortConnectionState


@runtime_checkable
class ComPortViewModelProtocol(Protocol):
    """Protocol defining the interface for COM port ViewModels."""

    # Core properties
    @property
    def port_number(self) -> int:
        """Return the port number identifier."""
        ...

    @property
    def port_label(self) -> str:
        """Return the human-readable port label."""
        ...

    @property
    def state(self) -> PortConnectionState:
        """Return the current port connection state."""
        ...

    @property
    def is_connected(self) -> bool:
        """Return whether the port is currently connected."""
        ...

    @property
    def port_name(self) -> Optional[str]:
        """Return the selected COM port name."""
        ...

    @property
    def baud_rate(self) -> int:
        """Return the current baud rate."""
        ...

    @property
    def rx_count(self) -> int:
        """Return RX counter value."""
        ...

    @property
    def tx_count(self) -> int:
        """Return TX counter value."""
        ...

    @property
    def error_count(self) -> int:
        """Return error counter value."""
        ...

    @property
    def available_ports(self) -> list:
        """Return list of available COM ports."""
        ...

    # Core methods
    def connect(self) -> bool:
        """Initiate connection to the port. Returns success status."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the port."""
        ...

    def send_data(self, data: str) -> bool:
        """Send data to the port. Returns success status."""
        ...

    def send_command(self, command: str) -> bool:
        """Send command to the port. Returns success status."""
        ...

    def clear_counters(self) -> None:
        """Reset RX and TX counters to zero."""
        ...

    def shutdown(self) -> None:
        """Clean shutdown of the port and worker."""
        ...

    # Setters
    def set_port_name(self, port_name: str) -> None:
        """Set the COM port name to connect to."""
        ...

    def set_baud_rate(self, baud_rate: int) -> None:
        """Set the baud rate."""
        ...

    def set_available_ports(self, ports: list) -> None:
        """Update list of available COM ports."""
        ...


@runtime_checkable
class CommandHistoryModelProtocol(Protocol):
    """Protocol defining the interface for command history."""

    @property
    def commands(self) -> list:
        """Return list of all commands."""
        ...

    def add_command(self, command: str) -> None:
        """Add a command to history."""
        ...

    def clear(self) -> None:
        """Clear command history."""
        ...

    def get_command(self, index: int) -> str:
        """Get command at index."""
        ...


class ViewModelFactoryProtocol(Protocol):
    """Protocol defining the interface for ViewModel factory."""

    def create_port_viewmodel(
        self,
        port_label: str,
        port_number: int,
    ) -> ComPortViewModelProtocol:
        """Create a port ViewModel instance."""
        ...

    def create_history_model(
        self,
        parent: Optional[object] = None,
    ) -> CommandHistoryModelProtocol:
        """Create a command history model instance."""
        ...


# Re-export for convenience
__all__ = [
    "ComPortViewModelProtocol",
    "CommandHistoryModelProtocol",
    "ViewModelFactoryProtocol",
]
