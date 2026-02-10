"""
Main window of the UART Control application.
MVVM Architecture: View layer for the application.
Integrates console logging with 3 serial ports, real-time counters, and search/filter functionality.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QMessageBox, QSplitter, QGroupBox, QFormLayout, QComboBox, QPushButton,
    QLineEdit, QCheckBox, QLabel, QTextEdit, QFrame, QGridLayout,
    QFileDialog
)
import os
import sys
import time
import datetime
import traceback

from src.utils.theme_manager import theme_manager
from src.utils.translator import translator, tr
from src.styles.constants import Colors, Fonts, Sizes, SerialConfig
from src.models.serial_worker import SerialWorker
from src.viewmodels.main_viewmodel import MainViewModel

try:
    from serial.tools import list_ports as list_serial_ports
    HAS_PYSERIAL = True
except Exception:
    HAS_PYSERIAL = False


class MainWindow(QMainWindow):
    """
    Main application window with integrated serial port logging.
    MVVM View that uses MainViewModel for business logic and SerialWorker for threading.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize ViewModel for logging and formatting
        self.viewmodel = MainViewModel()
        
        # Serial port workers
        self.workers = {}  # port_label -> SerialWorker
        self.connected_ports = {}  # port_label -> is_connected
        
        # Setup window properties
        self.setWindowTitle(tr("app_name", "UART Control"))
        self.setGeometry(100, 100, Sizes.WINDOW_DEFAULT_WIDTH, Sizes.WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        
        # Setup icon and UI
        self._set_window_icon()
        self._setup_ui()
        self._setup_menu()
        
        # Apply theme
        theme_manager.theme_changed.connect(self._on_theme_changed)
        theme_manager.apply_theme()
        
        # Connect language change signal
        translator.language_changed.connect(self._on_language_changed)
        
        # Setup status bar
        self.statusBar().showMessage(tr("ready", "Ready"))
        
        # Initialize port scanning
        self._scan_ports_all()
    
    def _setup_ui(self):
        """Initialize main UI components with three-panel layout."""
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create horizontal splitter for three-panel layout
        hsplit = QSplitter(Qt.Horizontal)
        
        # LEFT PANEL: Port settings and commands
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(Sizes.LAYOUT_SPACING)
        left_layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN, 
                                       Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # CPU1 Port Settings
        grp1 = self._create_port_group(tr("send_to_cpu1", "CPU1"), 1)
        left_layout.addWidget(grp1, 0)
        
        # CPU2 Port Settings
        grp2 = self._create_port_group(tr("send_to_cpu2", "CPU2"), 2)
        left_layout.addWidget(grp2, 0)
        
        # Data Transmission Group
        input_grp = self._create_transmission_group()
        left_layout.addWidget(input_grp, 0)
        
        # Status indicators
        status_grp = self._create_status_group()
        left_layout.addWidget(status_grp, 0)
        
        left_layout.addStretch()
        left_panel.setMinimumWidth(Sizes.LEFT_PANEL_MIN_WIDTH)
        left_panel.setMaximumWidth(Sizes.LEFT_PANEL_MAX_WIDTH)
        
        # CENTER PANEL: Logs
        center_panel = self._create_logs_panel()
        center_panel.setMinimumWidth(Sizes.CENTER_PANEL_MIN_WIDTH)
        
        # RIGHT PANEL: Counters and AUX
        right_panel = self._create_right_panel()
        right_panel.setMinimumWidth(Sizes.RIGHT_PANEL_MIN_WIDTH)
        right_panel.setMaximumWidth(Sizes.RIGHT_PANEL_MAX_WIDTH)
        
        # Assemble splitter
        hsplit.addWidget(left_panel)
        hsplit.addWidget(center_panel)
        hsplit.addWidget(right_panel)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 1)
        hsplit.setStretchFactor(2, 0)
        
        main_layout.addWidget(hsplit)
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def _create_port_group(self, label: str, port_num: int) -> QGroupBox:
        """Create a port settings group for CPU1 or CPU2."""
        grp = QGroupBox(label)
        layout = QFormLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Port combo
        port_combo = QComboBox()
        port_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        setattr(self, f'cb_port_{port_num}', port_combo)
        
        scan_btn = QPushButton(tr("scan", "Scan"))
        scan_btn.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        scan_btn.setMaximumWidth(Sizes.BUTTON_MAX_WIDTH)
        scan_btn.clicked.connect(lambda: self._scan_ports(port_num))
        setattr(self, f'btn_scan_{port_num}', scan_btn)
        
        port_layout = QHBoxLayout()
        port_layout.setSpacing(Sizes.LAYOUT_SPACING)
        port_layout.addWidget(port_combo, 1)
        port_layout.addWidget(scan_btn, 0)
        layout.addRow(tr("port", "Port:"), port_layout)
        
        # Baud combo
        baud_combo = QComboBox()
        baud_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        setattr(self, f'cb_baud_{port_num}', baud_combo)
        layout.addRow(tr("baud_rate", "Baud:"), baud_combo)
        
        # Connect button
        conn_btn = QPushButton(tr("connect", "Connect"))
        conn_btn.setMinimumHeight(Sizes.BUTTON_MIN_HEIGHT)
        conn_btn.clicked.connect(lambda: self._toggle_connection(port_num))
        setattr(self, f'btn_connect_{port_num}', conn_btn)
        layout.addRow(conn_btn)
        
        grp.setLayout(layout)
        return grp
    
    def _create_transmission_group(self) -> QGroupBox:
        """Create data transmission group with command input."""
        grp = QGroupBox(tr("data_transmission", "Data Transmission"))
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Command input
        self.le_command = QLineEdit()
        self.le_command.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self.le_command.setPlaceholderText(tr("enter_command", "Enter command..."))
        layout.addWidget(self.le_command)
        
        # Send buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Sizes.LAYOUT_SPACING)
        
        btn1 = QPushButton(tr("send_to_cpu1", "CPU1"))
        btn1.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn1.clicked.connect(lambda: self._send_command(1))
        self.btn_send_1 = btn1
        buttons_layout.addWidget(btn1, 1)
        
        btn2 = QPushButton(tr("send_to_cpu2", "CPU2"))
        btn2.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn2.clicked.connect(lambda: self._send_command(2))
        self.btn_send_2 = btn2
        buttons_layout.addWidget(btn2, 1)
        
        btn_both = QPushButton(tr("send_to_both", "1+2"))
        btn_both.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn_both.clicked.connect(lambda: self._send_command(0))
        self.btn_send_both = btn_both
        buttons_layout.addWidget(btn_both, 1)
        
        layout.addLayout(buttons_layout)
        grp.setLayout(layout)
        return grp
    
    def _create_status_group(self) -> QGroupBox:
        """Create status group."""
        grp = QGroupBox(tr("status", "Status"))
        layout = QFormLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        self.lbl_overall_status = QLabel(tr("disconnected", "Disconnected"))
        layout.addRow(tr("overall", "Overall:"), self.lbl_overall_status)
        
        grp.setLayout(layout)
        return grp
    
    def _create_logs_panel(self) -> QWidget:
        """Create center panel with logs and toolbar."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Toolbar for log management
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(Sizes.LAYOUT_SPACING)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search field
        search_label = QLabel(tr("search", "Search:"))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText(tr("search_logs", "Search logs..."))
        self.le_search.setMaximumWidth(Sizes.SEARCH_FIELD_MAX_WIDTH)
        self.le_search.textChanged.connect(self._on_search_changed)
        
        # Display options
        show_label = QLabel(tr("show", "Show:"))
        self.chk_time = QCheckBox(tr("time", "Time"))
        self.chk_time.setChecked(True)
        self.chk_time.stateChanged.connect(self._on_display_options_changed)
        
        self.chk_source = QCheckBox(tr("source", "Source"))
        self.chk_source.setChecked(True)
        self.chk_source.stateChanged.connect(self._on_display_options_changed)
        
        # Buttons
        self.btn_clear = QPushButton(tr("clear", "Clear"))
        self.btn_clear.setMaximumWidth(Sizes.BUTTON_CLEAR_MAX_WIDTH)
        self.btn_clear.clicked.connect(self._clear_all_logs)
        
        self.btn_save = QPushButton(tr("save", "Save"))
        self.btn_save.setMaximumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH)
        self.btn_save.clicked.connect(self._save_logs)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.le_search)
        toolbar_layout.addWidget(show_label)
        toolbar_layout.addWidget(self.chk_time)
        toolbar_layout.addWidget(self.chk_source)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_clear)
        toolbar_layout.addWidget(self.btn_save)
        
        layout.addLayout(toolbar_layout)
        
        # Create tabs for different views
        self.tab_logs = QTabWidget()
        
        # Tab 1: CPU1 and CPU2 side-by-side
        tab1 = QWidget()
        tab1_layout = QHBoxLayout(tab1)
        tab1_layout.setSpacing(Sizes.LAYOUT_SPACING)
        tab1_layout.setContentsMargins(0, 0, 0, 0)
        
        self.txt_log_cpu1_tab1 = self._create_log_widget()
        self.txt_log_cpu2_tab1 = self._create_log_widget()
        
        tab1_layout.addWidget(QLabel("CPU1:"), 0)
        tab1_layout.addWidget(self.txt_log_cpu1_tab1, 1)
        tab1_layout.addWidget(QLabel("CPU2:"), 0)
        tab1_layout.addWidget(self.txt_log_cpu2_tab1, 1)
        
        self.tab_logs.addTab(tab1, tr("combined", "1+2"))
        
        # Tab 2: CPU1 only
        self.txt_log_cpu1 = self._create_log_widget()
        self.tab_logs.addTab(self.txt_log_cpu1, tr("send_to_cpu1", "CPU1"))
        
        # Tab 3: CPU2 only
        self.txt_log_cpu2 = self._create_log_widget()
        self.tab_logs.addTab(self.txt_log_cpu2, tr("send_to_cpu2", "CPU2"))
        
        # Tab 4: All combined
        self.txt_log_all = self._create_log_widget()
        self.tab_logs.addTab(self.txt_log_all, tr("all", "All"))
        
        layout.addWidget(self.tab_logs, 1)
        panel.setLayout(layout)
        return panel
    
    def _create_log_widget(self) -> QTextEdit:
        """Create a read-only log text widget with monospace font."""
        widget = QTextEdit()
        widget.setReadOnly(True)
        widget.setFont(Fonts.get_monospace_font(9))
        return widget
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with counters and AUX log."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Counters group
        counters_grp = QGroupBox(tr("port_counters", "Port Counters"))
        counters_layout = QGridLayout()
        counters_layout.setSpacing(Sizes.LAYOUT_SPACING)
        counters_layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                          Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # CPU1
        self.lbl_cpu1_rx = QLabel("RX: 0")
        self.lbl_cpu1_tx = QLabel("TX: 0")
        counters_layout.addWidget(QLabel("CPU1:"), 0, 0)
        counters_layout.addWidget(self.lbl_cpu1_rx, 0, 1)
        counters_layout.addWidget(self.lbl_cpu1_tx, 0, 2)
        
        # CPU2
        self.lbl_cpu2_rx = QLabel("RX: 0")
        self.lbl_cpu2_tx = QLabel("TX: 0")
        counters_layout.addWidget(QLabel("CPU2:"), 1, 0)
        counters_layout.addWidget(self.lbl_cpu2_rx, 1, 1)
        counters_layout.addWidget(self.lbl_cpu2_tx, 1, 2)
        
        counters_grp.setLayout(counters_layout)
        layout.addWidget(counters_grp, 0)
        
        # AUX log
        aux_grp = QGroupBox("AUX Log")
        aux_layout = QVBoxLayout()
        aux_layout.setSpacing(Sizes.LAYOUT_SPACING)
        aux_layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                      Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        self.txt_log_aux = self._create_log_widget()
        aux_layout.addWidget(self.txt_log_aux)
        aux_grp.setLayout(aux_layout)
        layout.addWidget(aux_grp, 1)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def _setup_menu(self):
        """Setup application menu bar."""
        menubar = self.menuBar()
        menubar.clear()
        
        # File menu
        file_menu = menubar.addMenu(tr("file", "File"))
        
        save_action = file_menu.addAction(tr("save_logs", "Save Logs"))
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_logs)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction(tr("close", "Exit"))
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu(tr("view", "View"))
        
        # Language submenu
        language_menu = view_menu.addMenu(tr("language", "Language"))
        language_menu.addAction(tr("russian", "Russian"), 
                               lambda: translator.set_language("ru_RU"))
        language_menu.addAction(tr("english", "English"), 
                               lambda: translator.set_language("en_US"))
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu(tr("theme", "Theme"))
        theme_menu.addAction(tr("light_theme", "Light"), 
                            lambda: theme_manager.set_theme("light"))
        theme_menu.addAction(tr("dark_theme", "Dark"), 
                            lambda: theme_manager.set_theme("dark"))
        theme_menu.addAction(tr("system_theme", "System"), 
                            lambda: theme_manager.set_theme("system"))
        
        # Help menu
        help_menu = menubar.addMenu(tr("help_menu", "Help"))
        about_action = help_menu.addAction(tr("about", "About"))
        about_action.triggered.connect(self._show_about)
    
    def _set_window_icon(self):
        """Set window icon based on current theme."""
        try:
            icon_name = "icon_white.ico" if theme_manager.is_dark_theme() else "icon_black.ico"
            icon_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "assets", "icons", icon_name
            )
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
    
    def _on_theme_changed(self, theme):
        """Handle theme change event."""
        self._set_window_icon()
        self.statusBar().showMessage(f"{tr('theme', 'Theme')}: {theme}", 3000)
    
    def _on_language_changed(self, language):
        """Handle language change event - refresh UI text."""
        self.setWindowTitle(tr("app_name", "UART Control"))
        self._setup_menu()
        self.statusBar().showMessage(tr("ready", "Ready"), 3000)
    
    def _show_about(self):
        """Show about dialog."""
        about_text = f"""
        <b>{tr('app_name', 'UART Control')}</b><br><br>
        {tr('description', 'Modern COM port control application')}<br><br>
        <b>{tr('version', 'Version')}:</b> 1.0.0
        """
        QMessageBox.about(self, tr("about", "About"), about_text)
    
    # ==================== Connection Management ====================
    
    def _toggle_connection(self, port_num: int):
        """Toggle connection for a port."""
        port_label = f"CPU{port_num}"
        btn = getattr(self, f'btn_connect_{port_num}')
        
        if port_label in self.workers and self.workers[port_label].isRunning():
            # Disconnect
            self.workers[port_label].stop()
            del self.workers[port_label]
            self.connected_ports[port_label] = False
            btn.setText(tr("connect", "Connect"))
            self.statusBar().showMessage(f"{port_label}: {tr('disconnected', 'Disconnected')}")
        else:
            # Connect
            port = getattr(self, f'cb_port_{port_num}').currentText()
            baud = int(getattr(self, f'cb_baud_{port_num}').currentText())
            
            worker = SerialWorker(port_label)
            worker.configure(port, baud)
            worker.rx.connect(self._on_serial_rx)
            worker.status.connect(self._on_serial_status)
            worker.error.connect(self._on_serial_error)
            worker.start()
            
            self.workers[port_label] = worker
            self.connected_ports[port_label] = True
            btn.setText(tr("disconnect", "Disconnect"))
            self.statusBar().showMessage(f"{port_label}: {tr('connected', 'Connected')}")
    
    def _scan_ports(self, port_num: int):
        """Scan for available serial ports."""
        ports = self._get_available_ports()
        combo = getattr(self, f'cb_port_{port_num}')
        current = combo.currentText()
        combo.clear()
        combo.addItems(ports)
        
        # Restore previous selection if available
        index = combo.findText(current)
        if index >= 0:
            combo.setCurrentIndex(index)
        
        self.statusBar().showMessage(f"Found {len(ports)} port(s)", 3000)
    
    def _scan_ports_all(self):
        """Scan ports for all port combos at startup."""
        ports = self._get_available_ports()
        for port_num in [1, 2]:
            combo = getattr(self, f'cb_port_{port_num}', None)
            if combo:
                combo.addItems(ports)
    
    @staticmethod
    def _get_available_ports() -> list:
        """Get list of available serial ports."""
        if HAS_PYSERIAL:
            try:
                return [p.device for p in list_serial_ports.comports()]
            except Exception:
                pass
        
        # Fallback to common ports
        return SerialConfig.DEFAULT_PORTS
    
    # ==================== Serial Data Handlers ====================
    
    def _on_serial_rx(self, port_label: str, data: str):
        """Handle received data from serial port."""
        html = self.viewmodel.format_rx(port_label, data)
        if not html:
            return
        
        # Append to appropriate log widgets
        self._append_log(self.txt_log_all, html, 'all')
        
        if port_label == 'CPU1':
            self._append_log(self.txt_log_cpu1_tab1, html, 'cpu1_tab1')
            self._append_log(self.txt_log_cpu1, html, 'cpu1')
            rx_count = self.viewmodel.increment_rx(1)
            self.lbl_cpu1_rx.setText(f"RX: {rx_count}")
        elif port_label == 'CPU2':
            self._append_log(self.txt_log_cpu2_tab1, html, 'cpu2_tab1')
            self._append_log(self.txt_log_cpu2, html, 'cpu2')
            rx_count = self.viewmodel.increment_rx(2)
            self.lbl_cpu2_rx.setText(f"RX: {rx_count}")
    
    def _on_serial_status(self, port_label: str, message: str):
        """Handle status message from serial port."""
        html = self.viewmodel.format_system(port_label, message)
        self._append_log(self.txt_log_all, html, 'all')
    
    def _on_serial_error(self, port_label: str, error_msg: str):
        """Handle error from serial port."""
        html = self.viewmodel.format_system(port_label, f"ERROR: {error_msg}")
        self._append_log(self.txt_log_all, html, 'all')
    
    def _append_log(self, widget: QTextEdit, html_text: str, cache_key: str):
        """Append HTML to log widget and update cache."""
        if not html_text or not html_text.strip():
            return
        
        # Append to widget
        cursor = widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        widget.setTextCursor(cursor)
        widget.insertHtml(html_text)
        
        # Cache for filtering
        plain_text = self.viewmodel.strip_html(html_text)
        self.viewmodel.cache_log_line(cache_key, html_text, plain_text)
    
    # ==================== Data Transmission ====================
    
    def _send_command(self, which: int):
        """Send command to serial port(s)."""
        text = self.le_command.text().strip()
        if not text:
            return
        
        if which == 1 and 'CPU1' in self.workers:
            worker = self.workers['CPU1']
            worker.write(text)
            html = self.viewmodel.format_tx('CPU1', text)
            self._append_log(self.txt_log_cpu1_tab1, html, 'cpu1_tab1')
            self._append_log(self.txt_log_cpu1, html, 'cpu1')
            self._append_log(self.txt_log_all, html, 'all')
            tx_count = self.viewmodel.increment_tx(1)
            self.lbl_cpu1_tx.setText(f"TX: {tx_count}")
        
        elif which == 2 and 'CPU2' in self.workers:
            worker = self.workers['CPU2']
            worker.write(text)
            html = self.viewmodel.format_tx('CPU2', text)
            self._append_log(self.txt_log_cpu2_tab1, html, 'cpu2_tab1')
            self._append_log(self.txt_log_cpu2, html, 'cpu2')
            self._append_log(self.txt_log_all, html, 'all')
            tx_count = self.viewmodel.increment_tx(2)
            self.lbl_cpu2_tx.setText(f"TX: {tx_count}")
        
        elif which == 0:
            if 'CPU1' in self.workers:
                worker = self.workers['CPU1']
                worker.write(text)
                html = self.viewmodel.format_tx('CPU1', text)
                self._append_log(self.txt_log_cpu1_tab1, html, 'cpu1_tab1')
                self._append_log(self.txt_log_cpu1, html, 'cpu1')
                tx_count = self.viewmodel.increment_tx(1)
                self.lbl_cpu1_tx.setText(f"TX: {tx_count}")
            
            if 'CPU2' in self.workers:
                worker = self.workers['CPU2']
                worker.write(text)
                html = self.viewmodel.format_tx('CPU2', text)
                self._append_log(self.txt_log_cpu2_tab1, html, 'cpu2_tab1')
                self._append_log(self.txt_log_cpu2, html, 'cpu2')
                tx_count = self.viewmodel.increment_tx(2)
                self.lbl_cpu2_tx.setText(f"TX: {tx_count}")
            
            html = self.viewmodel.format_tx('BOTH', text)
            self._append_log(self.txt_log_all, html, 'all')
        
        self.le_command.clear()
    
    # ==================== Log Management ====================
    
    def _on_display_options_changed(self):
        """Handle display options change (time/source visibility)."""
        show_time = self.chk_time.isChecked()
        show_source = self.chk_source.isChecked()
        self.viewmodel.set_display_options(show_time, show_source)
        
        # Rebuild all logs from cache
        current_tab = self.tab_logs.currentIndex()
        if current_tab == 0:
            for cache_key, widget in [('cpu1_tab1', self.txt_log_cpu1_tab1), 
                                     ('cpu2_tab1', self.txt_log_cpu2_tab1)]:
                content = ''.join(self.viewmodel.log_cache.get(cache_key, {}).get('html', []))
                self._rebuild_log_widget(widget, content)
        elif current_tab == 1:
            content = ''.join(self.viewmodel.log_cache.get('cpu1', {}).get('html', []))
            self._rebuild_log_widget(self.txt_log_cpu1, content)
        elif current_tab == 2:
            content = ''.join(self.viewmodel.log_cache.get('cpu2', {}).get('html', []))
            self._rebuild_log_widget(self.txt_log_cpu2, content)
        elif current_tab == 3:
            content = ''.join(self.viewmodel.log_cache.get('all', {}).get('html', []))
            self._rebuild_log_widget(self.txt_log_all, content)
    
    def _on_search_changed(self, search_text: str):
        """Handle search field changes."""
        current_tab = self.tab_logs.currentIndex()
        
        if current_tab == 0:
            for cache_key, widget in [('cpu1_tab1', self.txt_log_cpu1_tab1),
                                     ('cpu2_tab1', self.txt_log_cpu2_tab1)]:
                content = self.viewmodel.filter_cache(cache_key, search_text)
                self._rebuild_log_widget(widget, content)
        elif current_tab == 1:
            content = self.viewmodel.filter_cache('cpu1', search_text)
            self._rebuild_log_widget(self.txt_log_cpu1, content)
        elif current_tab == 2:
            content = self.viewmodel.filter_cache('cpu2', search_text)
            self._rebuild_log_widget(self.txt_log_cpu2, content)
        elif current_tab == 3:
            content = self.viewmodel.filter_cache('all', search_text)
            self._rebuild_log_widget(self.txt_log_all, content)
    
    @staticmethod
    def _rebuild_log_widget(widget: QTextEdit, content: str):
        """Rebuild log widget with new content."""
        widget.blockSignals(True)
        widget.clear()
        if content:
            cursor = widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            widget.setTextCursor(cursor)
            widget.insertHtml(content)
        widget.blockSignals(False)
    
    def _clear_all_logs(self):
        """Clear all logs and cache."""
        self.txt_log_cpu1_tab1.clear()
        self.txt_log_cpu2_tab1.clear()
        self.txt_log_cpu1.clear()
        self.txt_log_cpu2.clear()
        self.txt_log_all.clear()
        self.txt_log_aux.clear()
        
        self.viewmodel.clear_cache()
        self.le_search.blockSignals(True)
        self.le_search.clear()
        self.le_search.blockSignals(False)
    
    def _save_logs(self):
        """Save current logs to file."""
        current_tab = self.tab_logs.currentIndex()
        
        if current_tab == 0:  # 1+2 tab
            text1 = self.txt_log_cpu1_tab1.toPlainText()
            text2 = self.txt_log_cpu2_tab1.toPlainText()
            text = f"=== CPU1 ===\n{text1}\n\n=== CPU2 ===\n{text2}"
            default_name = f"logs_1+2_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif current_tab == 1:
            text = self.txt_log_cpu1.toPlainText()
            default_name = f"logs_CPU1_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif current_tab == 2:
            text = self.txt_log_cpu2.toPlainText()
            default_name = f"logs_CPU2_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif current_tab == 3:
            text = self.txt_log_all.toPlainText()
            default_name = f"logs_all_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_logs", "Save Logs"), default_name, 
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, tr("success", "Success"), 
                                       f"{tr('logs_saved', 'Logs saved to')}:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, tr("error", "Error"), 
                                   f"{tr('failed_save', 'Failed to save logs')}:\n{str(e)}")
    
    def closeEvent(self, event):
        """Handle window close - disconnect all ports."""
        for port_label, worker in list(self.workers.items()):
            if worker.isRunning():
                worker.stop()
        event.accept()

