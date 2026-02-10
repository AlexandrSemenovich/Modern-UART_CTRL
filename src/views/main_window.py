"""
Main window of the UART Control application.
MVVM Architecture: View layer for the application.
Integrates console logging with 3 serial ports, real-time counters, and search/filter functionality.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QMessageBox, QSplitter, QGroupBox, QFormLayout, QComboBox, QPushButton,
    QLineEdit, QCheckBox, QLabel, QTextEdit, QFrame, QGridLayout,
    QFileDialog, QListWidget
)
import os
import sys
import time
import datetime
import traceback

from src.utils.theme_manager import theme_manager
from src.utils.translator import translator, tr
from src.styles.constants import Fonts, Sizes, SerialConfig
from src.models.serial_worker import SerialWorker
from src.viewmodels.main_viewmodel import MainViewModel

try:
    from serial.tools import list_ports as list_serial_ports
    HAS_PYSERIAL = True
except Exception:
    HAS_PYSERIAL = False


class PortWidgets:
    """Container for widgets of a single port."""
    def __init__(self, port_num: int):
        self.port_num = port_num
        self.port_combo: QComboBox = None
        self.scan_btn: QPushButton = None
        self.baud_combo: QComboBox = None
        self.connect_btn: QPushButton = None


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
        
        # Port widgets container (replaces dynamic setattr)
        self.port_widgets = {1: PortWidgets(1), 2: PortWidgets(2), 3: PortWidgets(3)}
        
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

        # Command history and shortcuts
        self.command_history: list[str] = []
        self.max_history = 20
        self.history_index = -1
        self.default_send_target = 0
        shortcut_send = QShortcut(QKeySequence("Ctrl+Enter"), self)
        shortcut_send.activated.connect(self._send_default_command)
        shortcut_cpu1 = QShortcut(QKeySequence("Ctrl+Alt+1"), self)
        shortcut_cpu1.activated.connect(lambda: self._send_command(1))
        shortcut_cpu2 = QShortcut(QKeySequence("Ctrl+Alt+2"), self)
        shortcut_cpu2.activated.connect(lambda: self._send_command(2))
        shortcut_tlm = QShortcut(QKeySequence("Ctrl+Alt+3"), self)
        shortcut_tlm.activated.connect(lambda: self._send_command(3))
        history_shortcut_up = QShortcut(QKeySequence("Ctrl+Up"), self)
        history_shortcut_down = QShortcut(QKeySequence("Ctrl+Down"), self)
        history_shortcut_up.activated.connect(lambda: self._navigate_history(-1))
        history_shortcut_down.activated.connect(lambda: self._navigate_history(1))
    
    def _setup_ui(self):
        """Initialize main UI components with three-panel layout and 3-console view."""
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
        
        # TLM Port Settings
        grp_tlm = self._create_port_group(tr("tlm", "TLM"), 3)
        left_layout.addWidget(grp_tlm, 0)
        
        # Data Transmission Group
        input_grp = self._create_transmission_group()
        left_layout.addWidget(input_grp, 0)
        
        left_layout.addStretch()
        left_panel.setMinimumWidth(Sizes.LEFT_PANEL_MIN_WIDTH)
        left_panel.setMaximumWidth(Sizes.LEFT_PANEL_MAX_WIDTH)
        
        # CENTER PANEL: All 3 console logs with adaptive splitter
        center_panel = self._create_consoles_panel()
        center_panel.setMinimumWidth(Sizes.CENTER_PANEL_MIN_WIDTH)
        
        # RIGHT PANEL: Counters
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
        
        # Get widgets container
        widgets = self.port_widgets[port_num]
        
        # Port combo
        port_combo = QComboBox()
        port_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        widgets.port_combo = port_combo
        
        scan_btn = QPushButton(tr("scan", "Scan"))
        scan_btn.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        scan_btn.setMaximumWidth(Sizes.BUTTON_MAX_WIDTH)
        scan_btn.clicked.connect(lambda: self._scan_ports(port_num))
        widgets.scan_btn = scan_btn
        
        port_layout = QHBoxLayout()
        port_layout.setSpacing(Sizes.LAYOUT_SPACING)
        port_layout.addWidget(port_combo, 1)
        port_layout.addWidget(scan_btn, 0)
        layout.addRow(tr("port", "Port:"), port_layout)
        
        # Baud combo
        baud_combo = QComboBox()
        baud_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        baud_combo.setCurrentText('115200')  # Default baud rate
        widgets.baud_combo = baud_combo
        layout.addRow(tr("baud_rate", "Baud:"), baud_combo)
        
        # Connect button
        conn_btn = QPushButton(tr("connect", "Connect"))
        conn_btn.setMinimumHeight(Sizes.BUTTON_MIN_HEIGHT)
        conn_btn.clicked.connect(lambda: self._toggle_connection(port_num))
        widgets.connect_btn = conn_btn
        layout.addRow(conn_btn)
        
        grp.setLayout(layout)
        return grp
    
    def _create_transmission_group(self) -> QGroupBox:
        """Create data transmission group with command input and send buttons."""
        grp = QGroupBox(tr("data_transmission", "Data Transmission"))
        self.grp_transmission = grp
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)

        # Command input
        input_layout = QHBoxLayout()
        self.le_command = QLineEdit()
        self.le_command.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self.le_command.setPlaceholderText(tr("enter_command", "Enter command..."))
        input_layout.addWidget(self.le_command, 1)
        layout.addLayout(input_layout)
        
        # Send buttons (4 buttons: 1+2, CPU1, CPU2, TLM)
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(Sizes.LAYOUT_SPACING)
        
        btn_combo = QPushButton(tr("send_to_both", "1+2"))
        btn_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn_combo.clicked.connect(lambda: self._send_command(0))
        self.btn_send_combo = btn_combo
        buttons_layout.addWidget(btn_combo, 0, 0)
        
        btn1 = QPushButton(tr("send_to_cpu1", "CPU1"))
        btn1.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn1.clicked.connect(lambda: self._send_command(1))
        self.btn_send_1 = btn1
        buttons_layout.addWidget(btn1, 0, 1)
        
        btn2 = QPushButton(tr("send_to_cpu2", "CPU2"))
        btn2.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn2.clicked.connect(lambda: self._send_command(2))
        self.btn_send_2 = btn2
        buttons_layout.addWidget(btn2, 1, 0)
        
        btn_tlm = QPushButton(tr("send_to_tlm", "TLM"))
        btn_tlm.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        btn_tlm.clicked.connect(lambda: self._send_command(3))
        self.btn_send_tlm = btn_tlm
        buttons_layout.addWidget(btn_tlm, 1, 1)

        layout.addLayout(buttons_layout)

        # Command history block
        history_layout = QVBoxLayout()
        history_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self.lbl_history_title = QLabel(tr("command_history", "Command History"))
        self.list_history = QListWidget()
        self.list_history.setMaximumHeight(150)
        self.list_history.itemDoubleClicked.connect(self._insert_history_command)

        history_controls = QHBoxLayout()
        self.btn_save_command = QPushButton(tr("save_command", "Save Command"))
        self.btn_save_command.setProperty("translation-key", "save_command")
        self.btn_save_command.clicked.connect(self._save_current_command)
        self.btn_clear_history = QPushButton(tr("clear_history", "Clear History"))
        self.btn_clear_history.setProperty("translation-key", "clear_history")
        self.btn_clear_history.clicked.connect(self._clear_history)
        history_controls.addWidget(self.btn_save_command)
        history_controls.addWidget(self.btn_clear_history)

        history_layout.addWidget(self.lbl_history_title)
        history_layout.addWidget(self.list_history)
        history_layout.addLayout(history_controls)
        layout.addLayout(history_layout)
        grp.setLayout(layout)
        return grp
    
    def _create_status_group(self) -> QGroupBox:
        """Create status group with per-port and TLM status."""
        grp = QGroupBox(tr("status", "Status"))
        layout = QFormLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        # Per-port status labels
        self.lbl_cpu1_status = QLabel(tr("disconnected", "Disconnected"))
        self.lbl_cpu2_status = QLabel(tr("disconnected", "Disconnected"))
        self.lbl_tlm_status = QLabel(tr("disconnected", "Disconnected"))
        self.lbl_overall_status = QLabel(tr("disconnected", "Disconnected"))

        layout.addRow(tr("cpu1", "CPU1:"), self.lbl_cpu1_status)
        layout.addRow(tr("cpu2", "CPU2:"), self.lbl_cpu2_status)
        layout.addRow(tr("tlm", "TLM:"), self.lbl_tlm_status)
        layout.addRow(tr("overall", "Overall:"), self.lbl_overall_status)
        
        grp.setLayout(layout)
        return grp
    
    def _create_consoles_panel(self) -> QWidget:
        """Create center panel with toolbar and tabbed logs (1+2, TLM, CPU1, CPU2)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Toolbar for log management
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(Sizes.TOOLBAR_SPACING)
        toolbar_layout.setContentsMargins(Sizes.TOOLBAR_MARGIN, Sizes.TOOLBAR_MARGIN,
                                          Sizes.TOOLBAR_MARGIN, Sizes.TOOLBAR_MARGIN)
        
        search_label = QLabel(tr("search", "Search:"))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText(tr("search_logs", "Search logs..."))
        self.le_search.setMaximumWidth(Sizes.SEARCH_FIELD_MAX_WIDTH)
        self.le_search.textChanged.connect(self._on_search_changed)
        
        show_label = QLabel(tr("show", "Show:"))
        self.chk_time = QCheckBox(tr("time", "Time"))
        self.chk_time.setChecked(True)
        self.chk_time.stateChanged.connect(self._on_display_options_changed)
        
        self.chk_source = QCheckBox(tr("source", "Source"))
        self.chk_source.setChecked(True)
        self.chk_source.stateChanged.connect(self._on_display_options_changed)
        
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
        
        # Tab widget with 1+2, TLM, CPU1, CPU2 tabs
        self.tab_logs = QTabWidget()
        self.tab_logs.setObjectName("tab_logs")
        self.tab_logs.setDocumentMode(True)
        
        # Tab 0: CPU1 + CPU2 combo
        combined_tab = QWidget()
        combined_layout = QHBoxLayout(combined_tab)
        combined_layout.setSpacing(Sizes.LAYOUT_SPACING)
        combined_layout.setContentsMargins(0, 0, 0, 0)
        
        cpu1_column = QVBoxLayout()
        cpu1_column.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self.txt_log_cpu1_tab1 = self._create_log_widget()
        cpu1_column.addWidget(QLabel(tr("send_to_cpu1", "CPU1")), 0)
        cpu1_column.addWidget(self.txt_log_cpu1_tab1, 1)
        
        cpu2_column = QVBoxLayout()
        cpu2_column.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self.txt_log_cpu2_tab1 = self._create_log_widget()
        cpu2_column.addWidget(QLabel(tr("send_to_cpu2", "CPU2")), 0)
        cpu2_column.addWidget(self.txt_log_cpu2_tab1, 1)
        
        combined_layout.addLayout(cpu1_column, 1)
        combined_layout.addLayout(cpu2_column, 1)
        self.tab_logs.addTab(combined_tab, tr("combined", "1+2"))
        
        # Tab 1: TLM
        tlm_tab = QWidget()
        tlm_layout = QVBoxLayout(tlm_tab)
        tlm_layout.setContentsMargins(0, 0, 0, 0)
        tlm_layout.setSpacing(Sizes.LAYOUT_SPACING)
        self.txt_log_tlm = self._create_log_widget()
        tlm_layout.addWidget(self._create_tab_header(tr("tlm", "TLM")))
        tlm_layout.addWidget(self.txt_log_tlm)
        self.tab_logs.addTab(tlm_tab, tr("tlm", "TLM"))
        
        # Tab 2: CPU1
        cpu1_tab = QWidget()
        cpu1_tab_layout = QVBoxLayout(cpu1_tab)
        cpu1_tab_layout.setContentsMargins(0, 0, 0, 0)
        cpu1_tab_layout.setSpacing(Sizes.LAYOUT_SPACING)
        self.txt_log_cpu1 = self._create_log_widget()
        cpu1_tab_layout.addWidget(self._create_tab_header(tr("send_to_cpu1", "CPU1")))
        cpu1_tab_layout.addWidget(self.txt_log_cpu1)
        self.tab_logs.addTab(cpu1_tab, tr("send_to_cpu1", "CPU1"))
        
        # Tab 3: CPU2
        cpu2_tab = QWidget()
        cpu2_tab_layout = QVBoxLayout(cpu2_tab)
        cpu2_tab_layout.setContentsMargins(0, 0, 0, 0)
        cpu2_tab_layout.setSpacing(Sizes.LAYOUT_SPACING)
        self.txt_log_cpu2 = self._create_log_widget()
        cpu2_tab_layout.addWidget(self._create_tab_header(tr("send_to_cpu2", "CPU2")))
        cpu2_tab_layout.addWidget(self.txt_log_cpu2)
        self.tab_logs.addTab(cpu2_tab, tr("send_to_cpu2", "CPU2"))
        
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
        """Create right panel with counters only (TLM moved to center)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                 Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # Counters group (CPU1, CPU2, TLM)
        counters_grp = QGroupBox(tr("port_counters", "Port Counters"))
        counters_layout = QGridLayout()
        counters_layout.setSpacing(Sizes.LAYOUT_SPACING)
        counters_layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
                                          Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        
        # CPU1
        self.lbl_cpu1_rx = QLabel(tr("rx_label", "RX: {count}").format(count=0))
        self.lbl_cpu1_tx = QLabel(tr("tx_label", "TX: {count}").format(count=0))
        counters_layout.addWidget(QLabel(tr("cpu1", "CPU1:")), 0, 0)
        counters_layout.addWidget(self.lbl_cpu1_rx, 0, 1)
        counters_layout.addWidget(self.lbl_cpu1_tx, 0, 2)
        
        # CPU2
        self.lbl_cpu2_rx = QLabel(tr("rx_label", "RX: {count}").format(count=0))
        self.lbl_cpu2_tx = QLabel(tr("tx_label", "TX: {count}").format(count=0))
        counters_layout.addWidget(QLabel(tr("cpu2", "CPU2:")), 1, 0)
        counters_layout.addWidget(self.lbl_cpu2_rx, 1, 1)
        counters_layout.addWidget(self.lbl_cpu2_tx, 1, 2)
        
        # TLM
        self.lbl_tlm_rx = QLabel(tr("rx_label", "RX: {count}").format(count=0))
        self.lbl_tlm_tx = QLabel(tr("tx_label", "TX: {count}").format(count=0))
        counters_layout.addWidget(QLabel(tr("tlm", "TLM:")), 2, 0)
        counters_layout.addWidget(self.lbl_tlm_rx, 2, 1)
        counters_layout.addWidget(self.lbl_tlm_tx, 2, 2)
        
        counters_grp.setLayout(counters_layout)
        layout.addWidget(counters_grp, 0)

        status_grp = self._create_status_group()
        layout.addWidget(status_grp, 0)
        
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
        self.statusBar().showMessage(
            tr("status_theme_changed", "Theme: {theme}").format(theme=theme),
            3000,
        )
    
    def _on_language_changed(self, language):
        """Handle language change event - refresh UI text."""
        # Rebuild main UI so all widgets pick up translations
        try:
            # Remove old central widget
            old = self.takeCentralWidget()
            if old is not None:
                old.deleteLater()
        except Exception:
            pass
        # Recreate UI and menu with translated texts
        self._setup_ui()
        self._setup_menu()
        # Update window title and brief status
        self.setWindowTitle(tr("app_name", "UART Control"))
        self.statusBar().showMessage(tr("ready", "Ready"), 3000)

        # Restore connect button texts based on current connection state
        try:
            for port_num in [1, 2, 3]:
                widgets = self.port_widgets.get(port_num)
                btn = widgets.connect_btn if widgets else None
                port_label = 'TLM' if port_num == 3 else f'CPU{port_num}'
                if btn is None:
                    continue
                if self.connected_ports.get(port_label):
                    btn.setText(tr("disconnect", "Disconnect"))
                else:
                    btn.setText(tr("connect", "Connect"))
        except Exception:
            pass
    
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
        """Toggle connection for a port (1=CPU1, 2=CPU2, 3=TLM)."""
        if port_num == 3:
            port_label = "TLM"
        else:
            port_label = f"CPU{port_num}"
        widgets = self.port_widgets.get(port_num)
        btn = widgets.connect_btn if widgets else None
        
        if port_label in self.workers and self.workers[port_label].isRunning():
            # Disconnect (request stop, UI will update on status signal)
            self.statusBar().showMessage(
                tr("status_port_message", "{port}: {message}").format(
                    port=port_label,
                    message=tr("disconnecting", "Disconnecting..."),
                )
            )
            btn.setEnabled(False)
            try:
                self.workers[port_label].stop()
            except Exception:
                pass
            # cleanup
            try:
                del self.workers[port_label]
            except Exception:
                pass
            self.connected_ports[port_label] = False
            btn.setText(tr("connect", "Connect"))
            btn.setEnabled(True)
        else:
            # Connect
            port = widgets.port_combo.currentText() if widgets else ""
            baud = int(widgets.baud_combo.currentText()) if widgets else 115200
            
            worker = SerialWorker(port_label)
            worker.configure(port, baud)
            worker.rx.connect(self._on_serial_rx)
            worker.status.connect(self._on_serial_status)
            worker.error.connect(self._on_serial_error)
            # Start async worker; status signals will confirm connection
            worker.start()

            self.workers[port_label] = worker
            self.connected_ports[port_label] = True
            btn.setText(tr("disconnect", "Disconnect"))
            # show initiating message, final status will come from worker
            self.statusBar().showMessage(
                tr("status_port_message", "{port}: {message}").format(
                    port=port_label,
                    message=tr("connecting", "Connecting..."),
                )
            )
    
    def _scan_ports(self, port_num: int):
        """Scan for available serial ports."""
        ports = self._get_available_ports()
        widgets = self.port_widgets.get(port_num)
        combo = widgets.port_combo if widgets else None
        current = combo.currentText() if combo else ""
        combo.clear()
        combo.addItems(ports)
        
        # Restore previous selection if available
        index = combo.findText(current)
        if index >= 0:
            combo.setCurrentIndex(index)
        
        self.statusBar().showMessage(
            tr("ports_found", "Found {count} port(s)").format(count=len(ports)),
            3000
        )
    
    def _scan_ports_all(self):
        """Scan ports for all port combos at startup."""
        ports = self._get_available_ports()
        for port_num in [1, 2, 3]:
            widgets = self.port_widgets.get(port_num)
            combo = widgets.port_combo if widgets else None
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
        """Handle received data from serial port (CPU1, CPU2, or TLM)."""
        html = self.viewmodel.format_rx(port_label, data)
        if not html:
            return
        
        # Append to appropriate log widgets
        if port_label == 'CPU1':
            self._append_log(self.txt_log_cpu1, html, 'cpu1')
            rx_count = self.viewmodel.increment_rx(1)
            self.lbl_cpu1_rx.setText(tr("rx_label", "RX: {count}").format(count=rx_count))
        elif port_label == 'CPU2':
            self._append_log(self.txt_log_cpu2, html, 'cpu2')
            rx_count = self.viewmodel.increment_rx(2)
            self.lbl_cpu2_rx.setText(tr("rx_label", "RX: {count}").format(count=rx_count))
        elif port_label == 'TLM':
            self._append_log(self.txt_log_tlm, html, 'tlm')
            rx_count = self.viewmodel.increment_rx(3)
            self.lbl_tlm_rx.setText(tr("rx_label", "RX: {count}").format(count=rx_count))
    
    def _on_serial_status(self, port_label: str, message: str):
        """Handle status message from serial port."""
        html = self.viewmodel.format_system(port_label, message)
        # Append to system log
        self._append_log(self.txt_log_cpu1, html, 'cpu1')

        # Update per-port and overall status labels and status bar
        try:
            if port_label == 'CPU1':
                self.lbl_cpu1_status.setText(message)
            elif port_label == 'CPU2':
                self.lbl_cpu2_status.setText(message)
            elif port_label == 'TLM':
                self.lbl_tlm_status.setText(message)
        except Exception:
            pass

        # Update overall status briefly
        try:
            self.lbl_overall_status.setText(message)
        except Exception:
            pass

        # Show transient status message to user
        try:
            self.statusBar().showMessage(
                tr("status_port_message", "{port}: {message}").format(
                    port=port_label,
                    message=message,
                ),
                5000,
            )
        except Exception:
            pass
    
    def _on_serial_error(self, port_label: str, error_msg: str):
        """Handle error from serial port."""
        html = self.viewmodel.format_system(port_label, f"ERROR: {error_msg}")
        self._append_log(self.txt_log_cpu1, html, 'cpu1')
        # Reflect error in UI labels and status bar
        try:
            error_text = tr("error_with_message", "Error: {message}").format(message=error_msg)
            if port_label == 'CPU1':
                self.lbl_cpu1_status.setText(error_text)
            elif port_label == 'CPU2':
                self.lbl_cpu2_status.setText(error_text)
            elif port_label == 'TLM':
                self.lbl_tlm_status.setText(error_text)
        except Exception:
            pass

        try:
            error_text = tr("error_with_message", "Error: {message}").format(message=error_msg)
            self.lbl_overall_status.setText(error_text)
        except Exception:
            pass

        try:
            self.statusBar().showMessage(
                tr("status_port_error", "Error ({port}): {message}").format(
                    port=port_label,
                    message=error_msg,
                ),
                8000,
            )
        except Exception:
            pass
    
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
        """Send command to serial port(s): 1=CPU1, 2=CPU2, 3=TLM, 0=All."""
        text = self.le_command.text().strip()
        if not text:
            return

        self._append_history(text)
        
        if which == 1 and 'CPU1' in self.workers:
            worker = self.workers['CPU1']
            worker.write(text)
            html = self.viewmodel.format_tx('CPU1', text)
            self._append_log(self.txt_log_cpu1, html, 'cpu1')
            tx_count = self.viewmodel.increment_tx(1)
            self.lbl_cpu1_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
        
        elif which == 2 and 'CPU2' in self.workers:
            worker = self.workers['CPU2']
            worker.write(text)
            html = self.viewmodel.format_tx('CPU2', text)
            self._append_log(self.txt_log_cpu2, html, 'cpu2')
            tx_count = self.viewmodel.increment_tx(2)
            self.lbl_cpu2_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
        
        elif which == 3 and 'TLM' in self.workers:
            worker = self.workers['TLM']
            worker.write(text)
            html = self.viewmodel.format_tx('TLM', text)
            self._append_log(self.txt_log_tlm, html, 'tlm')
            tx_count = self.viewmodel.increment_tx(3)
            self.lbl_tlm_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
        
        elif which == 0:  # Send to all 3
            if 'CPU1' in self.workers:
                worker = self.workers['CPU1']
                worker.write(text)
                html = self.viewmodel.format_tx('CPU1', text)
                self._append_log(self.txt_log_cpu1, html, 'cpu1')
                tx_count = self.viewmodel.increment_tx(1)
                self.lbl_cpu1_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
            
            if 'CPU2' in self.workers:
                worker = self.workers['CPU2']
                worker.write(text)
                html = self.viewmodel.format_tx('CPU2', text)
                self._append_log(self.txt_log_cpu2, html, 'cpu2')
                tx_count = self.viewmodel.increment_tx(2)
                self.lbl_cpu2_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
            
            if 'TLM' in self.workers:
                worker = self.workers['TLM']
                worker.write(text)
                html = self.viewmodel.format_tx('TLM', text)
                self._append_log(self.txt_log_tlm, html, 'tlm')
                tx_count = self.viewmodel.increment_tx(3)
                self.lbl_tlm_tx.setText(tr("tx_label", "TX: {count}").format(count=tx_count))
        
        self.le_command.clear()
    
    # ==================== Log Management ====================
    
    def _on_display_options_changed(self):
        """Handle display options change (time/source visibility)."""
        show_time = self.chk_time.isChecked()
        show_source = self.chk_source.isChecked()
        self.viewmodel.set_display_options(show_time, show_source)
        
        # Rebuild all 3 consoles from cache
        for cache_key, widget in [('cpu1', self.txt_log_cpu1),
                                  ('cpu2', self.txt_log_cpu2),
                                  ('tlm', self.txt_log_tlm)]:
            content = ''.join(self.viewmodel.log_cache.get(cache_key, {}).get('html', []))
            self._rebuild_log_widget(widget, content)
    
    def _on_search_changed(self, search_text: str):
        """Handle search field changes - search all 3 consoles."""
        for cache_key, widget in [('cpu1', self.txt_log_cpu1),
                                  ('cpu2', self.txt_log_cpu2),
                                  ('tlm', self.txt_log_tlm)]:
            content = self.viewmodel.filter_cache(cache_key, search_text)
            self._rebuild_log_widget(widget, content)
    
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
        self.txt_log_cpu1.clear()
        self.txt_log_cpu2.clear()
        self.txt_log_tlm.clear()
        
        self.viewmodel.clear_cache()
        self.le_search.blockSignals(True)
        self.le_search.clear()
        self.le_search.blockSignals(False)
    
    def _save_logs(self):
        """Save current logs to file - offers choice between combined or separate files."""
        text_cpu1 = self.txt_log_cpu1.toPlainText()
        text_cpu2 = self.txt_log_cpu2.toPlainText()
        text_tlm = self.txt_log_tlm.toPlainText()
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ask user: combined or separate files
        reply = QMessageBox.question(
            self,
            tr("save_logs", "Save Logs"),
            tr("save_logs_prompt", "Save as:\n1. Single file (all consoles)\n2. Separate files for each console"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        elif reply == QMessageBox.StandardButton.Yes:
            # Save combined file
            combined_text = """{title}\n{generated}\n\n{sep}\n{cpu1}\n{sep}\n{text_cpu1}\n\n{sep}\n{cpu2}\n{sep}\n{text_cpu2}\n\n{sep}\n{tlm}\n{sep}\n{text_tlm}\n""".format(
                title=tr("logs_combined_title", "=== {app_name} - Combined Logs ===").format(
                    app_name=tr("app_name", "UART Control")
                ),
                generated=tr("logs_generated", "Generated: {timestamp}").format(timestamp=timestamp),
                sep='=' * 50,
                cpu1=tr("logs_section_cpu1", "=== CPU1 ==="),
                cpu2=tr("logs_section_cpu2", "=== CPU2 ==="),
                tlm=tr("logs_section_tlm", "=== TLM (Telemetry) ==="),
                text_cpu1=text_cpu1,
                text_cpu2=text_cpu2,
                text_tlm=text_tlm
            )
            default_name = f"logs_combined_{timestamp}.txt"
            path, _ = QFileDialog.getSaveFileName(
                self, tr("save_logs", "Save Logs"), default_name, 
                "Text Files (*.txt);;All Files (*.*)"
            )
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(combined_text)
                    QMessageBox.information(self, tr("success", "Success"), 
                                           f"{tr('logs_saved', 'Logs saved to')}:\n{path}")
                except Exception as e:
                    QMessageBox.warning(self, tr("error", "Error"), 
                                       f"{tr('failed_save', 'Failed to save logs')}:\n{str(e)}")
        else:
            # Save separate files - user chooses directory
            from PySide6.QtWidgets import QFileDialog
            folder = QFileDialog.getExistingDirectory(
                self, tr("save_logs", "Save Logs")
            )
            if folder:
                try:
                    files_saved = []
                    if text_cpu1:
                        cpu1_path = os.path.join(folder, f"logs_CPU1_{timestamp}.txt")
                        with open(cpu1_path, 'w', encoding='utf-8') as f:
                            f.write(text_cpu1)
                        files_saved.append(cpu1_path)
                    
                    if text_cpu2:
                        cpu2_path = os.path.join(folder, f"logs_CPU2_{timestamp}.txt")
                        with open(cpu2_path, 'w', encoding='utf-8') as f:
                            f.write(text_cpu2)
                        files_saved.append(cpu2_path)
                    
                    if text_tlm:
                        tlm_path = os.path.join(folder, f"logs_TLM_{timestamp}.txt")
                        with open(tlm_path, 'w', encoding='utf-8') as f:
                            f.write(text_tlm)
                        files_saved.append(tlm_path)
                    
                    msg = tr("logs_saved_files", "Saved {count} file(s):\n{files}").format(
                        count=len(files_saved),
                        files="\n".join(files_saved)
                    )
                    QMessageBox.information(self, tr("success", "Success"), msg)
                except Exception as e:
                    QMessageBox.warning(self, tr("error", "Error"), 
                                       f"{tr('failed_save', 'Failed to save logs')}:\n{str(e)}")
    
    def closeEvent(self, event):
        """Handle window close - disconnect all ports."""
        # Stop all running workers and wait briefly for cleanup
        for port_label, worker in list(self.workers.items()):
            try:
                if worker.isRunning():
                    worker.stop()
            except Exception:
                pass
        # give threads a moment
        QtCore.QThread.msleep(100)
        event.accept()

    def _create_tab_header(self, title: str) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        label = QLabel(title)
        label.setProperty("class", "tab-label")
        layout.addWidget(label)
        layout.addStretch()
        return header
    def _send_default_command(self):
        self._send_command(self.default_send_target)

    def _navigate_history(self, direction: int):
        if direction not in (-1, 1) or not self.command_history:
            return
        self.history_index += direction
        self.history_index = max(0, min(len(self.command_history) - 1, self.history_index))
        try:
            self.le_command.setText(self.command_history[self.history_index])
        except Exception:
            pass

    def _append_history(self, command: str) -> None:
        if not command:
            return
        if self.command_history and self.command_history[-1] == command:
            self.history_index = len(self.command_history)
            return
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
            try:
                self.list_history.takeItem(0)
            except Exception:
                pass
        self.list_history.addItem(command)
        self.list_history.scrollToBottom()
        self.history_index = len(self.command_history)

    def _save_current_command(self) -> None:
        text = self.le_command.text().strip()
        self._append_history(text)

    def _clear_history(self) -> None:
        self.command_history.clear()
        self.history_index = -1
        self.list_history.clear()

    def _insert_history_command(self, item) -> None:
        try:
            self.le_command.setText(item.text())
        except Exception:
            pass
