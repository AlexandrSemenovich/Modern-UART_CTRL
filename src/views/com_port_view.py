"""
COM Port View - displays and manages a single COM port.
MVVM Architecture: View layer that binds to ComPortModel via ComPortViewModel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QComboBox, QPushButton, QTextEdit, QHBoxLayout, QLineEdit,
    QCheckBox, QFileDialog, QStyle
)
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtCore import Qt, Signal, QSize

from src.models.com_port_model import ComPortModel
from src.viewmodels.com_port_viewmodel import ComPortViewModel
from src.utils.translator import tr, translator
from src.utils.transmission_settings import load_settings, save_settings
from src.utils.transmission_settings import add_history_entry, clear_history as clear_history_settings
from src.utils.theme_manager import theme_manager
import os


class ComPortView(QWidget):
    """View for a single COM port (MVVM View layer)."""
    # signal to request a port scan from the container
    scan_requested = Signal()
    
    def __init__(self, model: ComPortModel, viewmodel: ComPortViewModel):
        super().__init__()
        self._model = model
        self._viewmodel = viewmodel
        # cache of last received data to compute diffs for timestamped appends
        self._last_received_cache = self._model.received_data or ""
        
        self._init_ui()
        self._connect_signals()
        # subscribe to model changes to update receive area
        try:
            self._model.received_data_changed.connect(self._on_received_data_changed)
        except Exception:
            pass
        
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
        self.baud_combo.setCurrentText("115200")
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
        
        # Data Transmission Group - modernized two-column layout
        data_group = QGroupBox(tr("data_transmission", "Data Transmission"))
        data_group.setMinimumHeight(300)
        data_layout = QHBoxLayout()
        data_layout.setSpacing(10)
        data_layout.setContentsMargins(8, 8, 8, 8)

        # Left: Received area (bigger)
        recv_layout = QVBoxLayout()
        recv_header = QHBoxLayout()
        self.recv_label = QLabel(tr("received_data", "Received Data:"))
        recv_header.addWidget(self.recv_label)
        recv_header.addStretch()
        self.recv_autoscroll_chk = QCheckBox(tr("autoscroll", "Auto-scroll"))
        self.recv_timestamp_chk = QCheckBox(tr("show_timestamps", "Show timestamps"))
        recv_header.addWidget(self.recv_autoscroll_chk)
        recv_header.addWidget(self.recv_timestamp_chk)
        recv_layout.addLayout(recv_header)

        self.recv_text = QTextEdit()
        self.recv_text.setReadOnly(True)
        self.recv_text.setPlaceholderText(tr("received_data", "Received data will appear here..."))
        recv_layout.addWidget(self.recv_text, 1)

        recv_footer = QHBoxLayout()
        self.save_btn = QPushButton(tr("save", "Save"))
        self.save_btn.setMinimumHeight(30)
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.clear_btn = QPushButton(tr("clear", "Clear"))
        self.clear_btn.setMinimumHeight(30)
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        recv_footer.addWidget(self.save_btn)
        recv_footer.addStretch()
        recv_footer.addWidget(self.clear_btn)
        recv_layout.addLayout(recv_footer)

        # Right: Send area (compact)
        send_layout = QVBoxLayout()
        send_header = QHBoxLayout()
        self.send_label = QLabel(tr("send_data", "Send Data:"))
        send_header.addWidget(self.send_label)
        send_header.addStretch()
        self.send_format_combo = QComboBox()
        self.send_format_combo.addItems([tr("ascii_view", "Text"), tr("hex_view", "Hex")])
        self.send_format_combo.setMinimumWidth(80)
        send_header.addWidget(self.send_format_combo)
        # command history combo
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.history_combo.setMinimumWidth(200)
        send_header.addWidget(self.history_combo)
        send_layout.addLayout(send_header)

        self.send_text = QLineEdit()
        self.send_text.setPlaceholderText(tr("send_data", "Enter data to send..."))
        send_layout.addWidget(self.send_text)

        send_options = QHBoxLayout()
        self.append_crlf_chk = QCheckBox(tr("append_newline", "Append newline"))
        send_options.addWidget(self.append_crlf_chk)
        send_options.addStretch()
        self.send_btn = QPushButton(tr("send", "Send"))
        self.send_btn.setMinimumHeight(30)
        try:
            self.send_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        except Exception:
            pass
        send_options.addWidget(self.send_btn)
        # save current command to history
        self.save_cmd_btn = QPushButton(tr("save_command", "Save Command"))
        self.save_cmd_btn.setMinimumHeight(30)
        send_options.addWidget(self.save_cmd_btn)
        self.clear_history_btn = QPushButton(tr("clear_history", "Clear History"))
        self.clear_history_btn.setMinimumHeight(30)
        send_options.addWidget(self.clear_history_btn)
        send_layout.addLayout(send_options)

        # Combine
        data_layout.addLayout(recv_layout, 3)
        data_layout.addLayout(send_layout, 1)

        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group, 1)
        
        self.setLayout(main_layout)
        # Load persisted transmission settings
        try:
            settings = load_settings()
            self.recv_autoscroll_chk.setChecked(bool(settings.get('autoscroll', True)))
            self.recv_timestamp_chk.setChecked(bool(settings.get('show_timestamps', False)))
            self.append_crlf_chk.setChecked(bool(settings.get('append_newline', False)))
            fmt = settings.get('send_format', 'text')
            idx = 0 if fmt == 'text' else 1
            if self.send_format_combo.count() > idx:
                self.send_format_combo.setCurrentIndex(idx)
            # populate history
            try:
                history = settings.get('history', []) or []
                for item in history:
                    self.history_combo.addItem(item)
            except Exception:
                pass
        except Exception:
            pass
        # prepare icons folder and set icons for buttons if available (theme-aware)
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            icons_dir = os.path.join(project_root, 'assets', 'icons')
            def _icon(name: str):
                # prefer FontAwesome folder, fall back to root icons
                fa_path = os.path.join(icons_dir, 'fa', name)
                p = fa_path if os.path.exists(fa_path) else os.path.join(icons_dir, name)
                return QIcon(p) if os.path.exists(p) else None

            def _apply_theme_icons():
                dark = theme_manager.is_dark_theme()
                suffix = 'dark' if dark else 'light'
                # try FontAwesome names first
                ic_send = _icon(f'paper-plane_{suffix}.svg') or _icon(f'send_{suffix}.svg') or _icon('paper-plane.svg') or _icon('send.svg')
                ic_save = _icon(f'floppy-disk_{suffix}.svg') or _icon(f'save_{suffix}.svg') or _icon('floppy-disk.svg') or _icon('save.svg')
                ic_clear = _icon(f'trash_{suffix}.svg') or _icon(f'clear_{suffix}.svg') or _icon('trash.svg') or _icon('clear.svg')
                ic_history = _icon(f'clock-rotate-left_{suffix}.svg') or _icon(f'history_{suffix}.svg') or _icon('clock-rotate-left.svg') or _icon('history.svg')
                ic_scan = _icon(f'magnifying-glass_{suffix}.svg') or _icon(f'scan_{suffix}.svg') or _icon('magnifying-glass.svg') or _icon('scan.svg')

                size = QSize(20, 20)
                if ic_send:
                    self.send_btn.setIcon(ic_send)
                    self.send_btn.setIconSize(size)
                if ic_save:
                    self.save_btn.setIcon(ic_save)
                    self.save_btn.setIconSize(size)
                    self.save_cmd_btn.setIcon(ic_save)
                    self.save_cmd_btn.setIconSize(size)
                if ic_clear:
                    self.clear_btn.setIcon(ic_clear)
                    self.clear_btn.setIconSize(size)
                    self.clear_history_btn.setIcon(ic_clear)
                    self.clear_history_btn.setIconSize(size)
                if ic_history:
                    self.history_combo.setToolTip(tr('command_history', 'Command History'))
                if ic_scan and hasattr(self, 'scan_btn'):
                    self.scan_btn.setIcon(ic_scan)
                    self.scan_btn.setIconSize(size)

            # initial apply
            _apply_theme_icons()
            # update when theme changes
            try:
                theme_manager.theme_changed.connect(lambda _: _apply_theme_icons())
            except Exception:
                pass
        except Exception:
            pass
    
    def _connect_signals(self):
        """Connect UI signals to slot methods."""
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.history_combo.activated.connect(self._on_history_selected)
        self.save_cmd_btn.clicked.connect(self._on_save_command_clicked)
        self.clear_history_btn.clicked.connect(self._on_clear_history_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        # persist UI settings when changed
        self.recv_autoscroll_chk.stateChanged.connect(self._save_ui_settings)
        self.recv_timestamp_chk.stateChanged.connect(self._save_ui_settings)
        self.append_crlf_chk.stateChanged.connect(self._save_ui_settings)
        self.send_format_combo.currentIndexChanged.connect(self._save_ui_settings)
        self.scan_btn.clicked.connect(self._on_scan_clicked)

    def _on_history_selected(self, index):
        try:
            text = self.history_combo.itemText(index)
            if text:
                self.send_text.setText(text)
        except Exception:
            pass

    def _on_save_command_clicked(self):
        try:
            # current send text
            entry = self.send_text.text() if hasattr(self.send_text, 'text') else self.send_text.toPlainText()
            if not entry or not entry.strip():
                return
            add_history_entry(entry)
            # refresh combo (prepend)
            try:
                self.history_combo.insertItem(0, entry)
            except Exception:
                pass
        except Exception:
            pass

    def _on_clear_history_clicked(self):
        try:
            clear_history_settings()
            self.history_combo.clear()
        except Exception:
            pass

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
        # support QLineEdit in the modernized UI
        if hasattr(self.send_text, 'text'):
            data = self.send_text.text()
        else:
            data = self.send_text.toPlainText()

        if data and data.strip():
            # apply append-newline option
            if getattr(self, 'append_crlf_chk', None) and self.append_crlf_chk.isChecked():
                data = data + "\r\n"

            # handle hex format if selected (try to convert to bytes)
            try:
                if getattr(self, 'send_format_combo', None) and self.send_format_combo.currentIndex() == 1:
                    # remove spaces and convert
                    hexstr = ''.join(data.split())
                    payload = bytes.fromhex(hexstr)
                else:
                    payload = data
            except Exception:
                payload = data

            try:
                self._viewmodel.send_data(payload)
            except Exception:
                # fallback to sending as string
                try:
                    self._viewmodel.send_data(str(payload))
                except Exception:
                    pass

            if hasattr(self.send_text, 'clear'):
                self.send_text.clear()

            # auto-scroll receive area if option set
            if getattr(self, 'recv_autoscroll_chk', None) and self.recv_autoscroll_chk.isChecked():
                try:
                    self.recv_text.moveCursor(QTextCursor.End)
                except Exception:
                    pass


    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.recv_text.clear()

    def _on_save_clicked(self):
        """Save received text to a file chosen by the user."""
        try:
            path, _ = QFileDialog.getSaveFileName(self, tr("save", "Save Received Data"), "", "Text Files (*.txt);;All Files (*)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.recv_text.toPlainText())
        except Exception:
            pass

    def _save_ui_settings(self):
        """Persist transmission UI settings to disk."""
        try:
            settings = {
                'autoscroll': bool(self.recv_autoscroll_chk.isChecked()),
                'show_timestamps': bool(self.recv_timestamp_chk.isChecked()),
                'append_newline': bool(self.append_crlf_chk.isChecked()),
                'send_format': 'text' if self.send_format_combo.currentIndex() == 0 else 'hex'
            }
            save_settings(settings)
        except Exception:
            pass

    def _on_received_data_changed(self):
        """Update receive text when model's received_data changes.

        We compute the diff against the cached value so we can optionally
        prefix new chunks with a timestamp.
        """
        try:
            new = self._model.received_data or ""
            old = self._last_received_cache or ""
            if new.startswith(old):
                diff = new[len(old):]
            else:
                diff = new

            if diff:
                if getattr(self, 'recv_timestamp_chk', None) and self.recv_timestamp_chk.isChecked():
                    from datetime import datetime
                    stamp = datetime.now().strftime("%H:%M:%S")
                    self.recv_text.append(f"[{stamp}] {diff}")
                else:
                    # append raw diff without clearing other text
                    self.recv_text.moveCursor(QTextCursor.End)
                    self.recv_text.insertPlainText(diff)

                if getattr(self, 'recv_autoscroll_chk', None) and self.recv_autoscroll_chk.isChecked():
                    try:
                        self.recv_text.moveCursor(QTextCursor.End)
                    except Exception:
                        pass

            self._last_received_cache = new
        except Exception:
            pass
    
    def _update_texts(self, language):
        """Update all UI texts when language changes."""
        # Update group box titles
        for widget in self.findChildren(QGroupBox):
            if widget.title() in [tr("port_settings", "Port Settings")]:
                widget.setTitle(tr("port_settings", "Port Settings"))
            elif widget.title() in [tr("data_transmission", "Data Transmission")]:
                widget.setTitle(tr("data_transmission", "Data Transmission"))
        
        # Update labels that we keep references to
        try:
            self.send_label.setText(tr("send_data", "Send Data:"))
            self.recv_label.setText(tr("received_data", "Received Data:"))
        except Exception:
            pass

        # update port-related labels (the earlier approach may still apply)
        labels = self.findChildren(QLabel)
        if len(labels) >= 5:
            labels[0].setText(tr("port_name", "Port:"))
            labels[1].setText(tr("baud_rate", "Baud Rate:"))
            labels[2].setText(tr("data_bits", "Data Bits:"))
            labels[3].setText(tr("parity", "Parity:"))
            labels[4].setText(tr("stop_bits", "Stop Bits:"))
        
        # Update button texts and new controls
        self.send_btn.setText(tr("send", "Send"))
        self.clear_btn.setText(tr("clear", "Clear"))
        self.save_btn.setText(tr("save", "Save"))
        # checkboxes and send format
        self.recv_autoscroll_chk.setText(tr("autoscroll", "Auto-scroll"))
        self.recv_timestamp_chk.setText(tr("show_timestamps", "Show timestamps"))
        self.append_crlf_chk.setText(tr("append_newline", "Append newline"))
        # send format combo
        try:
            self.send_format_combo.clear()
            self.send_format_combo.addItems([tr("ascii_view", "Text"), tr("hex_view", "Hex")])
        except Exception:
            pass
        
        # Update connect button based on state
        if self._viewmodel.is_connected:
            self.connect_btn.setText(tr("close_port", "Disconnect"))
        else:
            self.connect_btn.setText(tr("open_port", "Connect"))
        
        # Update placeholders
        self.send_text.setPlaceholderText(tr("send_data", "Enter data to send..."))
        self.recv_text.setPlaceholderText(tr("received_data", "Received data will appear here..."))
