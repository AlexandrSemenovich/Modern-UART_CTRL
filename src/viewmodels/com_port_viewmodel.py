"""
COM Port ViewModel - presentation logic for a COM port.
MVVM Architecture: ViewModel layer that binds Model to View.
"""

from PySide6.QtCore import QObject, Signal, Property

from src.models.com_port_model import ComPortModel
from src.utils.translator import tr


class ComPortViewModel(QObject):
    """ViewModel for a single COM port (MVVM ViewModel layer)."""
    
    # Signals
    connected_changed = Signal(bool)
    connection_status_changed = Signal(str)
    tx_requested = Signal(str)
    
    def __init__(self, model: ComPortModel):
        super().__init__()
        self._model = model
        self._is_connected = False
        self._connection_status = tr("disconnected", "Disconnected")
    
    def connect_port(self):
        """Connect to COM port."""
        try:
            self._model.set_open(True)
            self._is_connected = True
            self._connection_status = tr("connected", "Connected")
            self.connected_changed.emit(True)
            self.connection_status_changed.emit(self._connection_status)
        except Exception as e:
            self._model.set_error(str(e))
            self._connection_status = tr("error_with_message", "Error: {message}").format(message=str(e))
            self.connection_status_changed.emit(self._connection_status)
    
    def disconnect_port(self):
        """Disconnect from COM port."""
        try:
            self._model.set_open(False)
            self._is_connected = False
            self._connection_status = tr("disconnected", "Disconnected")
            self.connected_changed.emit(False)
            self.connection_status_changed.emit(self._connection_status)
        except Exception as e:
            self._model.set_error(str(e))
    
    def send_data(self, data: str):
        """Send data through COM port."""
        if self._is_connected:
            try:
                # Emit a signal so an external worker can perform actual transmission
                self.tx_requested.emit(data)
            except Exception as e:
                self._model.set_error(str(e))
    
    @Property(bool, notify=connected_changed)
    def is_connected(self):
        """Check if port is connected."""
        return self._is_connected
    
    @Property(str, notify=connection_status_changed)
    def connection_status(self):
        """Get connection status message."""
        return self._connection_status
