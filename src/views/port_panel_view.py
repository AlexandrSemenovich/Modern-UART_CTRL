"""
PortPanelView: UI component for a single COM port panel.
Reusable widget for port configuration and connection.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Signal, Qt, QTimer
from typing import Optional, List, Callable

from src.utils.translator import tr, translator
from src.utils.theme_manager import theme_manager
from src.styles.constants import Fonts, Sizes, SerialConfig, SerialPorts
from src.viewmodels.com_port_viewmodel import ComPortViewModel, PortConnectionState

try:
    from serial.tools import list_ports as list_serial_ports
    HAS_PYSERIAL = True
except Exception:
    HAS_PYSERIAL = False


class PortPanelView(QtWidgets.QGroupBox):
    """
    UI component for a single COM port panel.
    
    Features:
    - Port selection with scan button
    - Baud rate configuration
    - Connect/disconnect button
    - Status indicator
    
    Signals:
        connected (int): Port number when connected
        disconnected (int): Port number when disconnected
    """
    
    connected = Signal(int)  # port_number
    disconnected = Signal(int)  # port_number
    
    # Standard baud rates
    BAUD_RATES = ['9600', '19200', '38400', '57600', '115200', '230400', '460800']
    
    def __init__(
        self, 
        viewmodel: ComPortViewModel,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        """
        Initialize PortPanelView.
        
        Args:
            viewmodel: ComPortViewModel instance for this port
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._viewmodel = viewmodel
        self._port_number = viewmodel.port_number
        self._themed_buttons: List[QtWidgets.QPushButton] = []
        
        # Set label from viewmodel
        self.setTitle(viewmodel.port_label)
        
        self._setup_ui()
        self._connect_signals()
        self._connect_viewmodel_signals()
        self._update_from_viewmodel()
        translator.language_changed.connect(self.retranslate_ui)
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed()
        
        # Initial port scan
        QTimer.singleShot(100, self._scan_ports)
    
    def _setup_ui(self) -> None:
        """Create and arrange UI elements."""
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Port selection row
        port_layout = QtWidgets.QHBoxLayout()
        port_layout.setSpacing(Sizes.LAYOUT_SPACING)
        
        self._port_combo = QtWidgets.QComboBox()
        self._port_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._port_combo.setEditable(True)
        self._port_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        port_layout.addWidget(self._port_combo, 1)
        
        self._scan_btn = QtWidgets.QPushButton(tr("scan", "Scan"))
        self._scan_btn.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._scan_btn.setMaximumWidth(Sizes.BUTTON_MAX_WIDTH)
        self._register_button(self._scan_btn, "secondary")
        port_layout.addWidget(self._scan_btn, 0)
        
        self._lbl_port = QtWidgets.QLabel(tr("port", "Port:"))
        layout.addRow(self._lbl_port, port_layout)
        
        # Baud rate row
        self._baud_combo = QtWidgets.QComboBox()
        self._baud_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._baud_combo.addItems(self.BAUD_RATES)
        self._baud_combo.setCurrentText(str(SerialConfig.DEFAULT_BAUD))
        self._lbl_baud = QtWidgets.QLabel(tr("baud_rate", "Baud:"))
        layout.addRow(self._lbl_baud, self._baud_combo)
        
        # Connect button (full width)
        self._connect_btn = QtWidgets.QPushButton(tr("connect", "Connect"))
        self._connect_btn.setMinimumHeight(Sizes.BUTTON_MIN_HEIGHT)
        self._register_button(self._connect_btn, "primary")
        layout.addRow(self._connect_btn)
        
        # Status label
        self._status_label = QtWidgets.QPushButton(tr("disconnected", "Disconnected"))
        self._status_label.setEnabled(False)
        self._status_label.setObjectName("statusLabel")
        self._register_button(self._status_label)
        self._status_label.setMinimumHeight(24)
        self._status_label.setProperty("state", PortConnectionState.DISCONNECTED)
        layout.addRow(self._status_label)
        
        self.setLayout(layout)
    
    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        # Scan button
        self._scan_btn.clicked.connect(self._on_scan_clicked)
        
        # Port combo selection change
        self._port_combo.currentTextChanged.connect(self._on_port_selected)
        
        # Baud rate change
        self._baud_combo.currentTextChanged.connect(self._on_baud_changed)
        
        # Connect button
        self._connect_btn.clicked.connect(self._on_connect_clicked)
    
    def _connect_viewmodel_signals(self) -> None:
        """Connect ViewModel signals to UI update handlers."""
        self._viewmodel.state_changed.connect(self._on_state_changed)
        self._viewmodel.error_occurred.connect(self._on_error)
    
    def _update_from_viewmodel(self) -> None:
        """Update UI state from ViewModel."""
        # Update baud rate
        baud_index = self._baud_combo.findText(str(self._viewmodel.baud_rate))
        if baud_index >= 0:
            self._baud_combo.setCurrentIndex(baud_index)
        
        # Update status button
        self._update_status_ui(self._viewmodel.state)
    
    def _on_scan_clicked(self) -> None:
        """Handle scan button click - refresh port list."""
        self._scan_ports()
    
    def _scan_ports(self) -> List[str]:
        """
        Scan for available COM ports.
        
        Returns:
            List of available port names
        """
        ports = []
        
        if HAS_PYSERIAL:
            try:
                available = list_serial_ports.comports()
                ports = [
                    p.device
                    for p in available
                    if p.device.upper() not in SerialPorts.SYSTEM_PORTS
                ]
            except Exception as e:
                print(f"Error scanning ports: {e}")
                ports = []

        # Add placeholder if no ports found
        if not ports:
            # Create default options
            defaults = SerialConfig.DEFAULT_PORTS
            ports = [
                port
                for port in defaults
                if port.upper() not in SerialPorts.SYSTEM_PORTS
            ]
        
        # Update combo without blocking signals
        self._port_combo.blockSignals(True)
        current_text = self._port_combo.currentText()
        
        self._port_combo.clear()
        self._port_combo.addItems(ports)
        
        # Restore selection if still valid
        if current_text in ports:
            self._port_combo.setCurrentText(current_text)
        
        self._port_combo.blockSignals(False)
        
        # Update viewmodel
        self._viewmodel.set_available_ports(ports)
        
        return ports
    
    def _on_port_selected(self, port_name: str) -> None:
        """Handle port selection change."""
        self._viewmodel.set_port_name(port_name)
    
    def _on_baud_changed(self, baud_text: str) -> None:
        """Handle baud rate change."""
        try:
            baud = int(baud_text)
            self._viewmodel.set_baud_rate(baud)
        except ValueError:
            pass
    
    def _on_connect_clicked(self) -> None:
        """Handle connect/disconnect button click."""
        if self._viewmodel.is_connected:
            self._viewmodel.disconnect()
        else:
            # Ensure port is selected
            port_name = self._port_combo.currentText()
            if not port_name:
                self._scan_ports()
                port_name = self._port_combo.currentText()
            
            if port_name:
                self._viewmodel.set_port_name(port_name)
                self._viewmodel.connect()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    tr("warning", "Warning"),
                    tr("error_no_port", "No COM port available")
                )
    
    def _on_state_changed(self, state: str) -> None:
        """Handle ViewModel state change."""
        self._update_status_ui(state)
        
        if state == PortConnectionState.CONNECTED:
            self.connected.emit(self._port_number)
            self._connect_btn.setText(tr("disconnect", "Disconnect"))
        elif state == PortConnectionState.DISCONNECTED:
            self.disconnected.emit(self._port_number)
            self._connect_btn.setText(tr("connect", "Connect"))
        
        # Disable controls when connected
        is_connected = (state == PortConnectionState.CONNECTED)
        self._port_combo.setEnabled(not is_connected)
        self._scan_btn.setEnabled(not is_connected)
        self._baud_combo.setEnabled(not is_connected)
    
    def _update_status_ui(self, state: str) -> None:
        """Update status label based on connection state."""
        state_texts = {
            PortConnectionState.DISCONNECTED: tr("disconnected", "Disconnected"),
            PortConnectionState.CONNECTING: tr("connecting", "Connecting..."),
            PortConnectionState.CONNECTED: tr("connected", "Connected"),
            PortConnectionState.ERROR: tr("error", "Error"),
        }

        text = state_texts.get(state, state)
        self._status_label.setText(text)
        self._status_label.setProperty("state", state)
        self._refresh_status_style()

    def _on_error(self, formatted_error: str) -> None:
        """Handle error message from ViewModel."""
        # Error is handled centrally, but could show in status
        pass
    
    @property
    def viewmodel(self) -> ComPortViewModel:
        """Get the ViewModel for this panel."""
        return self._viewmodel
    
    def shutdown(self) -> None:
        """Clean shutdown of the panel."""
        self._viewmodel.shutdown()
    
    def setEnabled(self, enabled: bool) -> None:
        """Override setEnabled to also affect child widgets."""
        super().setEnabled(enabled)
        # Keep connect button enabled for disconnect
        if self._viewmodel.is_connected:
            self._connect_btn.setEnabled(True)

    def retranslate_ui(self) -> None:
        """Update all static texts when language changes."""
        self.setTitle(self._viewmodel.port_label)
        self._lbl_port.setText(tr("port", "Port:"))
        self._lbl_baud.setText(tr("baud_rate", "Baud:"))
        self._scan_btn.setText(tr("scan", "Scan"))
        self._le_command_placeholder = tr("enter_command", "Enter command...")
        self._connect_btn.setText(
            tr("disconnect", "Disconnect")
            if self._viewmodel.is_connected
            else tr("connect", "Connect")
        )
        self._update_status_ui(self._viewmodel.state)

    def _on_theme_changed(self, *_args) -> None:
        """Refresh status colors when global theme switches."""
        self._apply_theme_to_all_buttons()
        self._refresh_status_style()
        self._update_status_ui(self._viewmodel.state)

    def _refresh_status_style(self) -> None:
        """Force the status label to re-evaluate QSS rules."""
        self._refresh_widget_style(self._status_label)

    def _register_button(
        self,
        button: QtWidgets.QPushButton,
        class_name: Optional[str] = None,
    ) -> None:
        """Attach theme-aware styling to a button."""
        if class_name:
            existing = button.property("class")
            if existing:
                classes = set(str(existing).split())
                classes.add(class_name)
                button.setProperty("class", " ".join(sorted(classes)))
            else:
                button.setProperty("class", class_name)
        self._themed_buttons.append(button)
        self._apply_theme_to_button(button)

    def _apply_theme_to_all_buttons(self) -> None:
        """Update all registered buttons with the active theme class."""
        for button in self._themed_buttons:
            self._apply_theme_to_button(button)

    def _apply_theme_to_button(self, button: QtWidgets.QPushButton) -> None:
        theme_class = "dark" if theme_manager.is_dark_theme() else "light"
        button.setProperty("themeClass", theme_class)
        self._refresh_widget_style(button)

    def _refresh_widget_style(self, widget: QtWidgets.QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
