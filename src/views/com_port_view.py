"""
COM Port View - displays and manages a single COM port.
MVVM Architecture: View layer that binds to ComPortModel via ComPortViewModel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QComboBox, QPushButton, QTextEdit, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

from src.models.com_port_model import ComPortModel
from src.viewmodels.com_port_viewmodel import ComPortViewModel
from src.utils.translator import tr, translator


class ComPortView(QWidget):
    """View for a single COM port (MVVM View layer)."""
    # signal to request a port scan from the container
    scan_requested = Signal()
    
    def __init__(self, model: ComPortModel, viewmodel: ComPortViewModel):
        super().__init__()
        self._model = model
        self._viewmodel = viewmodel
        
        self._init_ui()
        self._connect_signals()
        
        # Connect language change signal
        translator.language_changed.connect(self._update_texts)
    
    def _init_ui(self):
        """Initialize UI components."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Port Configuration Group
        port_group = QGroupBox(tr("port_settings", "Port Settings"))
        port_group.setMinimumHeight(200)
        port_layout = QGridLayout()
        port_layout.setSpacing(8)
        port_layout.setContentsMargins(8, 8, 8, 8)
        
        # Port name with scan button
        port_layout.addWidget(QLabel(tr("port_name", "Port:")), 0, 0)
        hport = QHBoxLayout()
        hport.setSpacing(5)
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5"])
        self.port_combo.setObjectName('port_combo')
        self.port_combo.setMinimumHeight(28)
        self.scan_btn = QPushButton(tr('scan_ports', 'Scan'))
        self.scan_btn.setObjectName('btn_scan')
        self.scan_btn.setMinimumHeight(28)
        self.scan_btn.setMinimumWidth(70)
        hport.addWidget(self.port_combo, 1)
        hport.addWidget(self.scan_btn, 0)
        port_layout.addLayout(hport, 0, 1)
        
        # Baud rate
        port_layout.addWidget(QLabel(tr("baud_rate", "Baud Rate:")), 1, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        self.baud_combo.setMinimumHeight(28)
        port_layout.addWidget(self.baud_combo, 1, 1)
        
        # Data bits
        port_layout.addWidget(QLabel(tr("data_bits", "Data Bits:")), 2, 0)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        self.data_bits_combo.setMinimumHeight(28)
        port_layout.addWidget(self.data_bits_combo, 2, 1)
        
        # Parity
        port_layout.addWidget(QLabel(tr("parity", "Parity:")), 3, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.parity_combo.setMinimumHeight(28)
        port_layout.addWidget(self.parity_combo, 3, 1)
        
        # Stop bits
        port_layout.addWidget(QLabel(tr("stop_bits", "Stop Bits:")), 4, 0)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")
        self.stop_bits_combo.setMinimumHeight(28)
        port_layout.addWidget(self.stop_bits_combo, 4, 1)
        
        # Connect button
        self.connect_btn = QPushButton(tr("open_port", "Connect"))
        self.connect_btn.setMinimumHeight(40)
        port_layout.addWidget(self.connect_btn, 5, 0, 1, 2)
        
        # Stretch column 1 to fill available space
        port_layout.setColumnStretch(1, 1)
        
        port_group.setLayout(port_layout)
        main_layout.addWidget(port_group)
        
        # Data Transmission Group
        data_group = QGroupBox(tr("data_transmission", "Data Transmission"))
        data_group.setMinimumHeight(300)
        data_layout = QVBoxLayout()
        data_layout.setSpacing(8)
        data_layout.setContentsMargins(8, 8, 8, 8)
        
        # Send area
        data_layout.addWidget(QLabel(tr("send_data", "Send Data:")))
        self.send_text = QTextEdit()
        self.send_text.setMinimumHeight(60)
        self.send_text.setMaximumHeight(100)
        self.send_text.setPlaceholderText(tr("send_data", "Enter data to send..."))
        data_layout.addWidget(self.send_text)
        
        self.send_btn = QPushButton(tr("send", "Send"))
        self.send_btn.setMinimumHeight(35)
        data_layout.addWidget(self.send_btn)
        
        # Receive area
        data_layout.addWidget(QLabel(tr("received_data", "Received Data:")))
        self.recv_text = QTextEdit()
        self.recv_text.setReadOnly(True)
        self.recv_text.setMinimumHeight(80)
        self.recv_text.setPlaceholderText(tr("received_data", "Received data will appear here..."))
        data_layout.addWidget(self.recv_text, 1)
        
        # Clear receive button
        self.clear_btn = QPushButton(tr("clear", "Clear"))
        self.clear_btn.setMinimumHeight(35)
        data_layout.addWidget(self.clear_btn)
        
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group, 1)
        
        self.setLayout(main_layout)
    
    def _connect_signals(self):
        """Connect UI signals to slot methods."""
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.scan_btn.clicked.connect(self._on_scan_clicked)

    def _on_scan_clicked(self):
        """Emit signal to request container to scan ports."""
        try:
            self.scan_requested.emit()
        except Exception:
            pass
    
    def _on_connect_clicked(self):
        """Handle connect/disconnect button click."""
        port_name = self.port_combo.currentText()
        
        if not self._viewmodel.is_connected:
            # Connect
            baud_rate = int(self.baud_combo.currentText())
            data_bits = int(self.data_bits_combo.currentText())
            parity = self.parity_combo.currentText()
            stop_bits = float(self.stop_bits_combo.currentText())
            
            self._model.port_name = port_name
            self._model.baud_rate = baud_rate
            self._model.data_bits = data_bits
            self._model.parity = parity
            self._model.stop_bits = stop_bits
            
            self._viewmodel.connect_port()
            self.connect_btn.setText(tr("close_port", "Disconnect"))
        else:
            # Disconnect
            self._viewmodel.disconnect_port()
            self.connect_btn.setText(tr("open_port", "Connect"))
    
    def _on_send_clicked(self):
        """Handle send button click."""
        data = self.send_text.toPlainText()
        if data.strip():
            self._viewmodel.send_data(data)
            self.send_text.clear()
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.recv_text.clear()
    
    def _update_texts(self, language):
        """Update all UI texts when language changes."""
        # Update group box titles
        for widget in self.findChildren(QGroupBox):
            if widget.title() in [tr("port_settings", "Port Settings")]:
                widget.setTitle(tr("port_settings", "Port Settings"))
            elif widget.title() in [tr("data_transmission", "Data Transmission")]:
                widget.setTitle(tr("data_transmission", "Data Transmission"))
        
        # Update labels
        labels = self.findChildren(QLabel)
        for i, label in enumerate(labels):
            if i == 0:  # Port:
                label.setText(tr("port_name", "Port:"))
            elif i == 1:  # Baud Rate:
                label.setText(tr("baud_rate", "Baud Rate:"))
            elif i == 2:  # Data Bits:
                label.setText(tr("data_bits", "Data Bits:"))
            elif i == 3:  # Parity:
                label.setText(tr("parity", "Parity:"))
            elif i == 4:  # Stop Bits:
                label.setText(tr("stop_bits", "Stop Bits:"))
            elif i == 5:  # Send Data:
                label.setText(tr("send_data", "Send Data:"))
            elif i == 6:  # Received Data:
                label.setText(tr("received_data", "Received Data:"))
        
        # Update button texts
        self.send_btn.setText(tr("send", "Send"))
        self.clear_btn.setText(tr("clear", "Clear"))
        
        # Update connect button based on state
        if self._viewmodel.is_connected:
            self.connect_btn.setText(tr("close_port", "Disconnect"))
        else:
            self.connect_btn.setText(tr("open_port", "Connect"))
        
        # Update placeholders
        self.send_text.setPlaceholderText(tr("send_data", "Enter data to send..."))
        self.recv_text.setPlaceholderText(tr("received_data", "Received data will appear here..."))
