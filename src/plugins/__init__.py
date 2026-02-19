"""
Plugin system for the application.
Provides abstract base classes for extensible components.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class SerialPortDriver(ABC):
    """
    Abstract base class for serial port drivers.
    
    Implement this to provide custom serial communication backends.
    """

    @abstractmethod
    def connect(self, port: str, baud: int, **kwargs) -> bool:
        """
        Connect to the serial port.
        
        Args:
            port: Port name (e.g., 'COM1', '/dev/ttyUSB0')
            baud: Baud rate
            **kwargs: Additional driver-specific parameters
            
        Returns:
            True if connection successful
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        ...

    @abstractmethod
    def write(self, data: bytes) -> int:
        """
        Write data to the port.
        
        Args:
            data: Bytes to write
            
        Returns:
            Number of bytes written
        """
        ...

    @abstractmethod
    def read(self, size: int = 1) -> bytes:
        """
        Read data from the port.
        
        Args:
            size: Maximum number of bytes to read
            
        Returns:
            Bytes read
        """
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether port is connected."""
        ...


class DataProcessor(ABC):
    """
    Abstract base class for data processors.
    
    Implement this to provide custom data transformation,
    filtering, or analysis.
    """

    @abstractmethod
    def process(self, data: bytes) -> bytes:
        """
        Process incoming data.
        
        Args:
            data: Raw data bytes
            
        Returns:
            Processed data bytes
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset processor state."""
        ...


class UIExtension(ABC):
    """
    Abstract base class for UI extensions.
    
    Implement this to add custom UI components or panels.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the extension name."""
        ...

    @property
    @abstractmethod
    def widget(self) -> Any:
        """Return the Qt widget for this extension."""
        ...


class PluginRegistry:
    """
    Registry for managing plugins.
    """
    
    def __init__(self) -> None:
        self._drivers: dict[str, type[SerialPortDriver]] = {}
        self._processors: dict[str, type[DataProcessor]] = {}
        self._ui_extensions: dict[str, type[UIExtension]] = {}
    
    def register_driver(self, name: str, driver_class: type[SerialPortDriver]) -> None:
        """Register a serial port driver."""
        self._drivers[name] = driver_class
    
    def register_processor(self, name: str, processor_class: type[DataProcessor]) -> None:
        """Register a data processor."""
        self._processors[name] = processor_class
    
    def register_ui_extension(self, name: str, extension_class: type[UIExtension]) -> None:
        """Register a UI extension."""
        self._ui_extensions[name] = extension_class
    
    def get_driver(self, name: str) -> type[SerialPortDriver] | None:
        """Get a registered driver class."""
        return self._drivers.get(name)
    
    def get_processor(self, name: str) -> type[DataProcessor] | None:
        """Get a registered processor class."""
        return self._processors.get(name)
    
    def get_ui_extension(self, name: str) -> type[UIExtension] | None:
        """Get a registered UI extension class."""
        return self._ui_extensions.get(name)


# Global plugin registry
_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


__all__ = [
    "SerialPortDriver",
    "DataProcessor",
    "UIExtension",
    "PluginRegistry",
    "get_plugin_registry",
]
