"""
Main window of the UART Control application.
MVVM Architecture: View layer for the application.
Refactored to use reusable components.

Features:
- Console logging with 3 serial ports
- Real-time counters
- Search/filter functionality
- Command history
- Port management via ComPortViewModel
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QColor, QKeySequence, QShortcut, QActionGroup, QAction
from PySide6.QtWidgets import QSystemTrayIcon
from typing import Dict, Optional, List
import os
import platform
import sys
import time
import datetime

from src.utils.logger import get_logger
from src.utils.icon_cache import IconCache, get_icon
logger = get_logger(__name__)

# Windows API для кастомного title bar
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        HAS_WIN32_API = True
    except ImportError:
        HAS_WIN32_API = False
else:
    HAS_WIN32_API = False

from src.utils.theme_manager import theme_manager
from src.utils.windows11 import apply_windows_11_style, is_windows_11_or_later, GlobalHotkeyManager, VK, MOD_CONTROL, MOD_ALT, MOD_SHIFT
from src.utils.translator import translator, tr
from src.styles.constants import Fonts, Sizes, SerialConfig, FlashAnimation
from src.views.port_panel_view import PortPanelView
from src.views.console_panel_view import ConsolePanelView
from src.viewmodels.com_port_viewmodel import ComPortViewModel, PortConnectionState
from src.viewmodels.command_history_viewmodel import CommandHistoryModel
from src.views.command_history_dialog import CommandHistoryDialog


from PySide6.QtCore import QAbstractNativeEventFilter


class _GlobalHotkeyEventFilter(QAbstractNativeEventFilter):
    """Native event filter for handling global hotkey messages."""
    
    def __init__(self, hotkey_manager: GlobalHotkeyManager):
        super().__init__()
        self._hotkey_manager = hotkey_manager
    
    def nativeEventFilter(self, eventType, message):
        """Handle native Windows events."""
        # Check for WM_HOTKEY message
        if eventType == b"windows_generic_MSG":
            try:
                import ctypes
                from ctypes import wintypes
                
                # PySide6 6.x returns Shiboken VoidPtr - need to convert properly
                # Get the address as integer
                msg_ptr = int(message)
                if msg_ptr:
                    msg = ctypes.cast(msg_ptr, ctypes.POINTER(wintypes.MSG)).contents
                    if msg.message == 0x0312:  # WM_HOTKEY
                        if self._hotkey_manager.handle_message(msg.wParam):
                            return True, 0
            except Exception:
                pass  # Ignore errors in native event filter
        
        return False, 0


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window with integrated serial port logging.
    MVVM View that uses ComPortViewModel for each port's business logic.
    """
    
    def __init__(self):
        super().__init__()
        
        # Port ViewModels (one per port)
        self._port_viewmodels: Dict[int, ComPortViewModel] = {}
        self._port_views: Dict[int, PortPanelView] = {}
        self._port_states: Dict[int, PortConnectionState] = {}
        self._error_dialogs: List[QtWidgets.QMessageBox] = []
        self._themed_buttons: List[QtWidgets.QPushButton] = []
        
        # Console panel
        self._console_panel: Optional[ConsolePanelView] = None
        
        # System tray
        self._tray_icon: Optional[QSystemTrayIcon] = None
        
        # Toast notifications
        self._toast_manager = None
        
        # Command history
        self._history_model = CommandHistoryModel(self)
        self._history_dialog: Optional[CommandHistoryDialog] = None
        
        # Setup window properties
        self._setup_window()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._setup_tray()
        
        # Connect theme changes
        theme_manager.theme_changed.connect(self._on_theme_changed)
        # Тема уже применена в main.py, не применяем повторно
        
        # Connect language changes
        translator.language_changed.connect(self._on_language_changed)
        
        # Status bar
        self.statusBar().showMessage(tr("ready", "Ready"))
        
        # Language toggle in status bar
        self._lang_label = QtWidgets.QLabel(tr("lang", "Lang:"))
        self.statusBar().addPermanentWidget(self._lang_label)
        
        self._lang_btn = QtWidgets.QPushButton(translator.get_language().upper())
        self._lang_btn.setFixedWidth(40)
        self._lang_btn.setToolTip(tr("switch_language", "Click to switch language"))
        self._lang_btn.clicked.connect(self._toggle_language)
        self.statusBar().addPermanentWidget(self._lang_btn)
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(tr("app_name", "UART Control"))
        
        # Accessibility hints
        self.setAccessibleName(tr("app_name", "UART Control"))
        self.setAccessibleDescription("Main application window for UART serial port communication control")
        
        self.setGeometry(100, 100, Sizes.WINDOW_DEFAULT_WIDTH, Sizes.WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        self._set_window_icon()
        
        # Настройка кастомного title bar через Windows API (если доступно)
        self._setup_custom_title_bar()
    
    def _set_window_icon(self) -> None:
        """Set window icon from assets using IconCache."""
        icon = IconCache.get_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
    
    def _setup_custom_title_bar(self) -> None:
        """Настройка кастомного title bar для Windows 11+ через DWM API."""
        if not HAS_WIN32_API:
            return
        
        try:
            # Windows API константы
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMWA_CORNER_RADIUS = 33
            
            # Mica и corner radius константы из windows11
            from src.utils.windows11 import DWMSBT_MICA, WIN11_CORNER_ROUND, set_window_backdrop, set_window_rounded_corners, is_windows_11_or_later
            
            # Получаем HWND окна (после показа окна)
            def apply_title_bar_theme():
                try:
                    hwnd = int(self.winId())
                    if hwnd:
                        # 1. Включаем тёмный режим для title bar
                        value = ctypes.c_int(1 if theme_manager.is_dark_theme() else 0)
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            wintypes.HWND(hwnd),
                            DWMWA_USE_IMMERSIVE_DARK_MODE,
                            ctypes.byref(value),
                            ctypes.sizeof(value)
                        )
                        
                        # 2. Применяем Mica эффект (Windows 11 only)
                        if is_windows_11_or_later():
                            try:
                                set_window_backdrop(hwnd, DWMSBT_MICA)
                            except Exception:
                                pass
                            
                            # 3. Скруглённые углы (Windows 11)
                            try:
                                set_window_rounded_corners(hwnd, WIN11_CORNER_ROUND)
                            except Exception:
                                pass
                        
                        # 4. Пытаемся установить цвет caption (Windows 11 22H2+)
                        try:
                            DWMWA_CAPTION_COLOR = 35
                            if theme_manager.is_dark_theme():
                                caption_color = 0x020617  # наш тёмно-синий цвет
                            else:
                                caption_color = 0xf4f6fb  # наш светлый цвет
                            color_value = wintypes.DWORD(caption_color)
                            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                                wintypes.HWND(hwnd),
                                DWMWA_CAPTION_COLOR,
                                ctypes.byref(color_value),
                                ctypes.sizeof(color_value)
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # Применяем после показа окна
            QTimer.singleShot(100, apply_title_bar_theme)
            # Также применяем при смене темы
            theme_manager.theme_changed.connect(lambda: QTimer.singleShot(100, apply_title_bar_theme))
        except Exception:
            pass
    
    def _setup_tray(self) -> None:
        """Setup system tray icon with context menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self._tray_icon = QSystemTrayIcon(self)
        
        # Use IconCache for theme-aware tray icon
        tray_icon = IconCache.get_tray_icon()
        if not tray_icon.isNull():
            self._tray_icon.setIcon(tray_icon)
        else:
            # Fallback: use the application window icon
            app_icon = self.windowIcon()
            if not app_icon.isNull():
                self._tray_icon.setIcon(app_icon)
            else:
                logger.warning("No tray icon available")
                return
        
        # Create context menu
        tray_menu = QtWidgets.QMenu()
        
        show_action = tray_menu.addAction(tr("tray_show", "Show Window"))
        show_action.triggered.connect(self.show)
        show_action.triggered.connect(self.activateWindow)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction(tr("tray_quit", "Quit"))
        quit_action.triggered.connect(self.close)
        
        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.setToolTip(tr("app_name", "UART Control"))
        
        # Double-click to show window
        self._tray_icon.activated.connect(self._on_tray_activated)
        
        self._tray_icon.show()
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show()
            self.activateWindow()
    
    def closeEvent(self, event) -> None:
        """Handle window close event - hide to tray or shutdown."""
        # Cleanup global hotkeys
        if hasattr(self, '_hotkey_manager') and self._hotkey_manager:
            self._hotkey_manager.cleanup()
        
        if self._tray_icon and self._tray_icon.isVisible():
            event.ignore()
            self.hide()
            return
        
        # Flush command history to disk before shutting down
        try:
            if hasattr(self, "_history_model") and self._history_model is not None:
                self._history_model.flush()
        except Exception:
            pass
        
        # Shutdown all port ViewModels
        for viewmodel in self._port_viewmodels.values():
            viewmodel.shutdown()
        
        # Give threads time to finish
        self._wait_for_threads()
        
        event.accept()
    
    def _setup_ui(self) -> None:
        """Initialize main UI components."""
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal splitter for panels
        hsplit = QtWidgets.QSplitter(Qt.Horizontal)
        
        # LEFT PANEL: Port controls
        left_panel = self._create_left_panel()
        left_panel.setMinimumWidth(Sizes.LEFT_PANEL_MIN_WIDTH)
        left_panel.setMaximumWidth(Sizes.LEFT_PANEL_MAX_WIDTH)
        left_panel.setObjectName("left_panel")
        hsplit.addWidget(left_panel)
        
        # CENTER PANEL: Console logs
        self._console_panel = ConsolePanelView()
        self._console_panel.setMinimumWidth(Sizes.CENTER_PANEL_MIN_WIDTH)
        self._console_panel.setObjectName("console_panel")
        hsplit.addWidget(self._console_panel)
        
        # RIGHT PANEL: Counters
        self._right_panel = self._create_right_panel()
        self._right_panel.setMinimumWidth(Sizes.RIGHT_PANEL_MIN_WIDTH)
        self._right_panel.setMaximumWidth(Sizes.RIGHT_PANEL_MAX_WIDTH)
        self._right_panel.setObjectName("right_panel")
        hsplit.addWidget(self._right_panel)
        
        # Set stretch factors
        hsplit.setStretchFactor(0, 0)  # Left - fixed
        hsplit.setStretchFactor(1, 1)  # Center - expandable
        hsplit.setStretchFactor(2, 0)  # Right - fixed
        
        main_layout.addWidget(hsplit)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Apply current theme classes to all widgets in the hierarchy
        self._apply_theme_to_hierarchy()
        
        # Apply Windows 11 visual effects (rounded corners, Mica)
        self._apply_windows11_effects()
        
        # Setup global hotkeys (Windows only)
        self._setup_global_hotkeys()
        
        # Connect console signals
        self._console_panel.clear_requested.connect(self._clear_all_logs)
        self._console_panel.save_requested.connect(self._save_logs)
    
    def _create_left_panel(self) -> QtWidgets.QWidget:
        """Create left panel with port controls wrapped in a scroll area."""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Create ViewModels and Views for each port
        port_ids = [
            (1, "cpu1"),
            (2, "cpu2"),
            (3, "tlm"),
        ]

        for port_num, port_key in port_ids:
            port_label = tr(port_key, port_key.upper())
            # Create ViewModel
            viewmodel = ComPortViewModel(port_label, port_num)
            self._port_viewmodels[port_num] = viewmodel
            self._port_states[port_num] = viewmodel.state
             
            # Create View
            port_view = PortPanelView(viewmodel)
            self._port_views[port_num] = port_view
            
            layout.addWidget(port_view)
            
            # Connect ViewModel signals to console (using bound methods to avoid lambda closure issues)
            # Use Qt.QueuedConnection for thread-safe handling of high-frequency serial data
            viewmodel.data_received.connect(
                self._make_rx_handler(port_key),
                type=Qt.QueuedConnection
            )
            viewmodel.data_sent.connect(
                self._make_tx_handler(port_key),
                type=Qt.QueuedConnection
            )
            viewmodel.error_occurred.connect(
                self._make_error_handler(port_key, viewmodel),
                type=Qt.QueuedConnection
            )
            viewmodel.state_changed.connect(
                self._make_state_handler(port_num),
                type=Qt.QueuedConnection
            )
            # Connect counter update signal
            viewmodel.counter_updated.connect(
                self._make_counter_handler(port_num, port_key),
                type=Qt.QueuedConnection
            )

        # Command input section
        command_group = self._create_command_group()
        layout.addWidget(command_group)
        self._update_command_controls()

        layout.addStretch()
        content.setLayout(layout)
        scroll_area.setWidget(content)
        
        return scroll_area
    
    def _create_command_group(self) -> QtWidgets.QGroupBox:
        """Create command input group."""
        grp = QtWidgets.QGroupBox(tr("data_transmission", "Data Transmission"))
        self._command_group = grp
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Command input
        input_layout = QtWidgets.QHBoxLayout()
        self._le_command = QtWidgets.QLineEdit()
        self._le_command.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._le_command.setPlaceholderText(tr("enter_command", "Enter command..."))
        self._le_command.setAccessibleName(tr("cmd_input_a11y", "Command input"))
        self._le_command.setAccessibleDescription(tr("cmd_input_desc_a11y", "Enter serial command to send"))
        self._le_command.returnPressed.connect(self._send_default_command)
        input_layout.addWidget(self._le_command, 1)
        layout.addLayout(input_layout)
        
        # Send buttons grid
        buttons_layout = QtWidgets.QGridLayout()
        buttons_layout.setSpacing(Sizes.LAYOUT_SPACING)
        buttons_layout.setColumnStretch(0, 1)
        buttons_layout.setColumnStretch(1, 1)
        buttons_layout.setRowStretch(0, 1)
        buttons_layout.setRowStretch(1, 1)

        # 1+2 button (send to both CPU1 and CPU2)
        self._btn_combo = QtWidgets.QPushButton(tr("send_to_both", "1+2"))
        self._btn_combo.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._btn_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._btn_combo.setAccessibleName(tr("btn_combo_a11y", "Send to all (1+2)"))
        self._btn_combo.setAccessibleDescription(tr("btn_combo_desc_a11y", "Click to send command to both CPU1 and CPU2 simultaneously"))
        self._register_button(self._btn_combo, "primary")
        self._btn_combo.setProperty("semanticRole", "command_combo")
        self._btn_combo.style().unpolish(self._btn_combo)
        self._btn_combo.style().polish(self._btn_combo)
        self._btn_combo.clicked.connect(lambda: self._send_command(0))
        buttons_layout.addWidget(self._btn_combo, 0, 0)

        # CPU1 button
        self._btn_cpu1 = QtWidgets.QPushButton(tr("send_to_cpu1", "CPU1"))
        self._btn_cpu1.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._btn_cpu1.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._btn_cpu1.setAccessibleName(tr("btn_cpu1_a11y", "Send to CPU1"))
        self._btn_cpu1.setAccessibleDescription(tr("btn_cpu1_desc_a11y", "Click to send command to CPU1"))
        self._register_button(self._btn_cpu1, "secondary")
        self._btn_cpu1.setProperty("semanticRole", "command_cpu1")
        self._btn_cpu1.clicked.connect(lambda: self._send_command(1))
        buttons_layout.addWidget(self._btn_cpu1, 0, 1)

        # CPU2 button
        self._btn_cpu2 = QtWidgets.QPushButton(tr("send_to_cpu2", "CPU2"))
        self._btn_cpu2.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._btn_cpu2.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._btn_cpu2.setAccessibleName(tr("btn_cpu2_a11y", "Send to CPU2"))
        self._btn_cpu2.setAccessibleDescription(tr("btn_cpu2_desc_a11y", "Click to send command to CPU2"))
        self._register_button(self._btn_cpu2, "secondary")
        self._btn_cpu2.setProperty("semanticRole", "command_cpu2")
        self._btn_cpu2.clicked.connect(lambda: self._send_command(2))
        buttons_layout.addWidget(self._btn_cpu2, 1, 0)

        # TLM button
        self._btn_tlm = QtWidgets.QPushButton(tr("send_to_tlm", "TLM"))
        self._btn_tlm.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._btn_tlm.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._btn_tlm.setAccessibleName(tr("btn_tlm_a11y", "Send to TLM"))
        self._btn_tlm.setAccessibleDescription(tr("btn_tlm_desc_a11y", "Click to send command to TLM"))
        self._register_button(self._btn_tlm, "secondary")
        self._btn_tlm.setProperty("semanticRole", "command_tlm")
        self._btn_tlm.clicked.connect(lambda: self._send_command(3))
        buttons_layout.addWidget(self._btn_tlm, 1, 1)
        
        layout.addLayout(buttons_layout)
        
        # Command history
        history_layout = QtWidgets.QVBoxLayout()
        history_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        
        summary_layout = QtWidgets.QHBoxLayout()
        summary_layout.setSpacing(Sizes.LAYOUT_SPACING)

        self._lbl_history_title = QtWidgets.QLabel(tr("command_history", "Command History"))
        summary_layout.addWidget(self._lbl_history_title)

        self._lbl_history_count = QtWidgets.QLabel()
        summary_layout.addWidget(self._lbl_history_count)

        summary_layout.addStretch(1)

        self._btn_open_history = QtWidgets.QToolButton()
        self._btn_open_history.setIcon(get_icon("clock-rotate-left"))
        self._btn_open_history.setText(tr("history_open", "History"))
        self._btn_open_history.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # Increase button size for better visibility
        self._btn_open_history.setMinimumSize(100, Sizes.BUTTON_MIN_HEIGHT)
        self._btn_open_history.setIconSize(QtCore.QSize(20, 20))
        self._register_button(self._btn_open_history, "ghost")
        self._btn_open_history.clicked.connect(self._open_history_dialog)
        summary_layout.addWidget(self._btn_open_history)

        history_layout.addLayout(summary_layout)
        layout.addLayout(history_layout)
        
        grp.setLayout(layout)
        return grp
    
    def _create_right_panel(self) -> QtWidgets.QWidget:
        """Create right panel with counters wrapped in a scroll area."""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Counters group - restructured for better readability
        counters_grp = QtWidgets.QGroupBox(tr("port_counters", "Port Counters"))
        counters_layout = QtWidgets.QVBoxLayout()  # Vertical layout for ports
        counters_layout.setSpacing(16)  # More spacing between ports
        counters_layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Counter labels
        self._counter_labels: Dict[str, QtWidgets.QLabel] = {}
        
        self._counter_ports = ["cpu1", "cpu2", "tlm"]

        self._counter_label_widgets: List[QtWidgets.QLabel] = []

        for port_key in self._counter_ports:
            # Create a card-like container for each port
            port_card = QtWidgets.QFrame()
            port_card.setObjectName("counter_card")
            port_card.setStyleSheet("""
                QFrame#counter_card {
                    background: palette(base);
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            port_card_layout = QtWidgets.QVBoxLayout(port_card)
            port_card_layout.setSpacing(4)
            port_card_layout.setContentsMargins(12, 8, 12, 8)
            
            # Port header
            port_name = tr(port_key, port_key.upper())
            port_header = QtWidgets.QLabel(
                tr("port_label_template", "{name}").format(name=port_name)
            )
            port_header.setProperty("translation_key", port_key)
            font = port_header.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            port_header.setFont(font)
            self._counter_label_widgets.append(port_header)
            port_card_layout.addWidget(port_header)
            
            # Metrics row 1: RX | TX
            metrics_row1 = QtWidgets.QHBoxLayout()
            metrics_row1.setSpacing(16)
            
            rx_label = QtWidgets.QLabel(
                tr("rx_label", "RX: {count}").format(count=0)
            )
            tx_label = QtWidgets.QLabel(
                tr("tx_label", "TX: {count}").format(count=0)
            )
            
            metrics_row1.addWidget(rx_label)
            metrics_row1.addWidget(tx_label)
            metrics_row1.addStretch()
            port_card_layout.addLayout(metrics_row1)
            
            # Metrics row 2: Errors | Time
            metrics_row2 = QtWidgets.QHBoxLayout()
            metrics_row2.setSpacing(16)
            
            error_label = QtWidgets.QLabel(
                tr("error_label", "Errors: {count}").format(count=0)
            )
            time_label = QtWidgets.QLabel(
                tr("time_label", "Time: {time}s").format(time=0)
            )
            
            metrics_row2.addWidget(error_label)
            metrics_row2.addWidget(time_label)
            metrics_row2.addStretch()
            port_card_layout.addLayout(metrics_row2)
            
            # Add card to counters layout
            counters_layout.addWidget(port_card)
            
            self._counter_labels[f"{port_key}_rx"] = rx_label
            self._counter_labels[f"{port_key}_tx"] = tx_label
            self._counter_labels[f"{port_key}_error"] = error_label
            self._counter_labels[f"{port_key}_time"] = time_label
        
        counters_grp.setLayout(counters_layout)
        layout.addWidget(counters_grp)
        
        layout.addStretch()
        content.setLayout(layout)
        scroll_area.setWidget(content)
        
        return scroll_area
    
    def _create_status_group(self) -> QtWidgets.QGroupBox:
        """Legacy status group removed from UI."""
        grp = QtWidgets.QGroupBox()
        grp.hide()
        return grp
    
    def _toggle_right_panel(self) -> None:
        """Toggle visibility of the right panel (counters)."""
        if hasattr(self, '_right_panel') and self._right_panel is not None:
            is_visible = self._right_panel.isVisible()
            self._right_panel.setVisible(not is_visible)
    
    def _setup_menu(self) -> None:
        """Setup application menu bar."""
        menubar = self.menuBar()
        menubar.clear()
        
        self._language_actions: Dict[str, QtGui.QAction] = {}

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
        language_group = QActionGroup(self)
        language_group.setExclusive(True)

        action_ru = language_menu.addAction(tr("russian", "Russian"))
        action_ru.setCheckable(True)
        language_group.addAction(action_ru)
        action_ru.triggered.connect(lambda: translator.set_language("ru_RU"))
        self._language_actions["ru_RU"] = action_ru

        action_en = language_menu.addAction(tr("english", "English"))
        action_en.setCheckable(True)
        language_group.addAction(action_en)
        action_en.triggered.connect(lambda: translator.set_language("en_US"))
        self._language_actions["en_US"] = action_en

        view_menu.addSeparator()

        # Theme submenu
        theme_menu = view_menu.addMenu(tr("theme", "Theme"))
        theme_menu.addAction(tr("light_theme", "Light"), 
                            lambda: theme_manager.set_theme("light"))
        theme_menu.addAction(tr("dark_theme", "Dark"), 
                            lambda: theme_manager.set_theme("dark"))
        theme_menu.addAction(tr("system_theme", "System"), 
                            lambda: theme_manager.set_theme("system"))
        
        # Scale submenu
        scale_menu = view_menu.addMenu(tr("scale", "Scale"))
        scale_menu.addAction("100%", lambda: self._set_ui_scale(1.0))
        scale_menu.addAction("125%", lambda: self._set_ui_scale(1.25))
        scale_menu.addAction("150%", lambda: self._set_ui_scale(1.5))
        scale_menu.addAction("175%", lambda: self._set_ui_scale(1.75))
        scale_menu.addAction("200%", lambda: self._set_ui_scale(2.0))

    # Maximum number of error dialogs to keep
    _MAX_ERROR_DIALOGS = 5
    
    def _handle_port_error(self, port_label: str, viewmodel: ComPortViewModel, message: str) -> None:
        plain_msg = message
        if '<' in message:
            import re
            plain_msg = re.sub('<.*?>', '', message)
        if self._console_panel:
            self._console_panel.append_system(port_label, plain_msg)
        
        # Use toast notification instead of blocking dialog
        if not self._toast_manager:
            from src.views.toast_notification import get_toast_manager
            self._toast_manager = get_toast_manager(self)
        
        self._toast_manager.show_toast(
            f"{port_label}: {plain_msg}",
            toast_type="error",
            duration_ms=5000
        )
    
    def _cleanup_error_dialog(self, dialog: QtWidgets.QMessageBox) -> None:
        """Remove closed dialog from tracking list."""
        if dialog in self._error_dialogs:
            self._error_dialogs.remove(dialog)
            dialog.deleteLater()
    
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Send with Ctrl+Enter
        shortcut_send = QShortcut(QKeySequence("Ctrl+Enter"), self)
        shortcut_send.activated.connect(self._send_default_command)
        
        # Port selection shortcuts
        shortcut_cpu1 = QShortcut(QKeySequence("Ctrl+Alt+1"), self)
        shortcut_cpu1.activated.connect(lambda: self._send_command(1))
        
        shortcut_cpu2 = QShortcut(QKeySequence("Ctrl+Alt+2"), self)
        shortcut_cpu2.activated.connect(lambda: self._send_command(2))
        
        shortcut_tlm = QShortcut(QKeySequence("Ctrl+Alt+3"), self)
        shortcut_tlm.activated.connect(lambda: self._send_command(3))
        
        # History dialog
        shortcut_history = QShortcut(QKeySequence("Ctrl+H"), self)
        shortcut_history.activated.connect(self._open_history_dialog)
        
        # Toggle right panel (Ctrl+R)
        shortcut_right_panel = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_right_panel.activated.connect(self._toggle_right_panel)
        
        # Clear console (Ctrl+L)
        shortcut_clear = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_clear.activated.connect(self._clear_all_logs)
        
        # Find in console (Ctrl+F)
        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self._toggle_console_search)
        
        # Reconnect all ports (Ctrl+F5)
        shortcut_reconnect = QShortcut(QKeySequence("Ctrl+F5"), self)
        shortcut_reconnect.activated.connect(self._reconnect_all_ports)
    
    def _send_command(self, port_num: int) -> None:
        """
        Send command to specified port(s).
        
        Args:
            port_num: Port number (0=all, 1=CPU1, 2=CPU2, 3=TLM)
        """
        command = self._le_command.text()
        if not command:
            return
        
        # Get button(s) to animate for visual feedback
        buttons_to_animate = self._get_buttons_for_port(port_num)
        
        # Add to history
        self._history_model.add_entry(command, self._port_label_for_num(port_num))
        
        # Send to port(s)
        if port_num == 0:
            # Send to CPU1 and CPU2
            for num in [1, 2]:
                if num in self._port_viewmodels:
                    self._port_viewmodels[num].send_command(command)
        elif port_num in self._port_viewmodels:
            self._port_viewmodels[port_num].send_command(command)
        
        # Visual feedback - animate button(s) to show TX activity
        self._animate_buttons_flash(buttons_to_animate)
        
        # Also animate command input field for additional feedback
        self._animate_command_input_flash()
    
    def _get_buttons_for_port(self, port_num: int) -> list:
        """Get buttons that correspond to the given port number for animation."""
        buttons = []
        if port_num == 0:  # combo - both CPU1 and CPU2
            buttons = [self._btn_combo, self._btn_cpu1, self._btn_cpu2]
        elif port_num == 1:
            buttons = [self._btn_cpu1]
        elif port_num == 2:
            buttons = [self._btn_cpu2]
        elif port_num == 3:
            buttons = [self._btn_tlm]
        return [b for b in buttons if b is not None]
    
    def _animate_buttons_flash(self, buttons: list) -> None:
        """
        Animate button flash to provide visual feedback when command is sent.
        Uses theme-aware subtle colors for a professional look.
        """
        if not buttons:
            return
        
        # Get theme-aware colors from constants
        is_dark = theme_manager.is_dark_theme()
        flash_style = FlashAnimation.get_button_flash_style(is_dark)
        
        # Store original styles
        original_styles = []
        for btn in buttons:
            original_styles.append(btn.styleSheet())
        
        # Apply flash effect
        for btn in buttons:
            btn.setStyleSheet(flash_style)
        
        # Restore original style after duration from constants
        def restore_styles():
            for btn, original in zip(buttons, original_styles):
                if btn:
                    btn.setStyleSheet(original)
        
        QTimer.singleShot(FlashAnimation.FLASH_DURATION_MS, restore_styles)
    
    def _animate_command_input_flash(self) -> None:
        """
        Animate command input field to provide visual feedback when command is sent.
        Uses theme-aware subtle colors for a professional look.
        """
        if not hasattr(self, '_le_command') or not self._le_command:
            return
        
        # Store original style
        original_style = self._le_command.styleSheet()
        
        # Get theme-aware colors from constants (matches button colors)
        is_dark = theme_manager.is_dark_theme()
        flash_style = FlashAnimation.get_input_flash_style(is_dark)
        
        self._le_command.setStyleSheet(flash_style)
        
        # Restore original style after duration from constants
        def restore_style():
            if self._le_command:
                self._le_command.setStyleSheet(original_style)
        
        QTimer.singleShot(FlashAnimation.FLASH_DURATION_MS, restore_style)
    
    def _send_default_command(self) -> None:
        """Send command to default port (CPU1)."""
        self._send_command(1)
    
    def _port_label_for_num(self, port_num: int) -> str:
        if port_num == 0:
            return "combo"
        return {1: "cpu1", 2: "cpu2", 3: "tlm"}.get(port_num, "unknown")

    def _open_history_dialog(self) -> None:
        if not self._history_dialog:
            self._history_dialog = CommandHistoryDialog(self._history_model, self)
            self._history_dialog.command_selected.connect(self._le_command.setText)
        self._history_dialog.show()
        self._history_dialog.raise_()
        self._history_dialog.activateWindow()
        self._update_history_summary()

    def _update_history_summary(self) -> None:
        count = self._history_model.entry_count()
        self._lbl_history_count.setText(
            tr("history_total", "{count} entries").format(count=count)
        )
    def _on_port_state_changed(self, port_num: int, state: str | PortConnectionState) -> None:
        """Track port connection state and refresh command controls."""
        normalized = self._normalize_state(state)
        self._port_states[port_num] = normalized
        self._update_command_controls()

    def _make_rx_handler(self, port_key: str):
        """Create a bound handler for RX data signal to avoid lambda closure issues."""
        def handler(data: str):
            self._console_panel.append_rx(tr(port_key, port_key.upper()), data)
        return handler

    def _make_tx_handler(self, port_key: str):
        """Create a bound handler for TX data signal to avoid lambda closure issues."""
        def handler(data: str):
            self._console_panel.append_tx(tr(port_key, port_key.upper()), data)
        return handler

    def _make_error_handler(self, port_key: str, viewmodel):
        """Create a bound handler for error signal to avoid lambda closure issues."""
        def handler(msg: str):
            self._handle_port_error(tr(port_key, port_key.upper()), viewmodel, msg)
        return handler

    def _make_state_handler(self, port_num: int):
        """Create a bound handler for state changed signal to avoid lambda closure issues."""
        def handler(state):
            self._on_port_state_changed(port_num, state)
        return handler

    def _make_counter_handler(self, port_num: int, port_key: str):
        """Create a bound handler for counter update signal."""
        def handler(rx_count: int, tx_count: int):
            self._on_counter_updated(port_num, port_key, rx_count, tx_count)
        return handler

    def _on_counter_updated(self, port_num: int, port_key: str, rx_count: int, tx_count: int) -> None:
        """Handle counter update signal - update counter labels in UI."""
        rx_label = self._counter_labels.get(f"{port_key}_rx")
        tx_label = self._counter_labels.get(f"{port_key}_tx")
        error_label = self._counter_labels.get(f"{port_key}_error")
        time_label = self._counter_labels.get(f"{port_key}_time")
        
        if rx_label:
            rx_label.setText(
                tr("rx_label", "RX: {count}").format(count=rx_count)
            )
        if tx_label:
            tx_label.setText(
                tr("tx_label", "TX: {count}").format(count=tx_count)
            )
        
        # Update error count and connection time from ViewModel
        viewmodel = self._port_viewmodels.get(port_num)
        if viewmodel:
            if error_label:
                error_label.setText(
                    tr("error_label", "Errors: {count}").format(count=viewmodel.error_count)
                )
            if time_label:
                conn_time = viewmodel.connection_time
                time_label.setText(
                    tr("time_label", "Time: {time}s").format(time=int(conn_time))
                )

    def _normalize_state(self, state: str | PortConnectionState) -> PortConnectionState:
        if isinstance(state, PortConnectionState):
            return state
        candidate = str(state).split('.')[-1].lower()
        for option in PortConnectionState:
            if option.value == candidate or option.name.lower() == candidate:
                return option
        return PortConnectionState.DISCONNECTED

    def _update_command_controls(self) -> None:
        """Enable send buttons only when their ports are connected."""
        if not hasattr(self, "_btn_cpu1"):
            return

        cpu1_connected = self._port_states.get(1) == PortConnectionState.CONNECTED
        cpu2_connected = self._port_states.get(2) == PortConnectionState.CONNECTED
        tlm_connected = self._port_states.get(3) == PortConnectionState.CONNECTED
        cpu1_connecting = self._port_states.get(1) == PortConnectionState.CONNECTING
        cpu2_connecting = self._port_states.get(2) == PortConnectionState.CONNECTING
        tlm_connecting = self._port_states.get(3) == PortConnectionState.CONNECTING

        self._apply_command_button_state(self._btn_cpu1, cpu1_connected, cpu1_connecting)
        self._apply_command_button_state(self._btn_cpu2, cpu2_connected, cpu2_connecting)
        self._apply_command_button_state(self._btn_tlm, tlm_connected, tlm_connecting)
        self._apply_command_button_state(
            self._btn_combo,
            cpu1_connected and cpu2_connected,
            cpu1_connecting or cpu2_connecting,
        )

    def _apply_command_button_state(
        self,
        button: QtWidgets.QPushButton,
        is_active: bool,
        is_connecting: bool,
    ) -> None:
        button.setEnabled(is_active or is_connecting)
        button.setProperty("dataActive", "true" if is_active else "false")
        button.setProperty(
            "dataState",
            "connecting" if is_connecting and not is_active else "default",
        )
        self._refresh_widget_style(button)
    
    def _clear_all_logs(self) -> None:
        """Clear all console logs with confirmation."""
        reply = QtWidgets.QMessageBox.question(
            self,
            tr("confirm_clear", "Confirm Clear"),
            tr("confirm_clear_message", "Are you sure you want to clear all logs? This action cannot be undone."),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            if self._console_panel:
                self._console_panel.clear_all()
    
    def _toggle_console_search(self) -> None:
        """Toggle the console search bar visibility."""
        if self._console_panel:
            self._console_panel.toggle_search_bar()
    
    def _reconnect_all_ports(self) -> None:
        """Reconnect all disconnected ports."""
        for port_num, viewmodel in self._port_viewmodels.items():
            if not viewmodel.is_connected:
                viewmodel.connect()
    
    def _set_ui_scale(self, scale_factor: float) -> None:
        """Set the UI scale factor for the application."""
        from PySide6 import QtWidgets
        from src.styles.constants import Fonts
        
        app = QtWidgets.QApplication.instance()
        if app:
            # Get font sizes from config (with scale factor applied)
            default_size = int(Fonts.get_default_size_pt() * scale_factor)
            button_size = int(Fonts.get_button_size_pt() * scale_factor)
            caption_size = int(Fonts.get_caption_size_pt() * scale_factor)
            monospace_size = int(Fonts.get_monospace_size_pt() * scale_factor)
            
            # Set the application-wide scale factor with proper typography hierarchy
            app.setStyleSheet(f"""
                QWidget {{
                    font-size: {default_size}pt;
                }}
                QPushButton {{
                    font-size: {button_size}pt;
                }}
                QLabel {{
                    font-size: {default_size}pt;
                }}
                QLineEdit {{
                    font-size: {default_size}pt;
                }}
                QTextEdit {{
                    font-size: {default_size}pt;
                }}
                QComboBox {{
                    font-size: {default_size}pt;
                }}
                /* Console uses larger monospace font for readability */
                QTextEdit[objectName^="console"] {{
                    font-size: {monospace_size}pt;
                }}
                /* Status bar and captions use smaller font */
                QStatusBar, QLabel[class~="caption"] {{
                    font-size: {caption_size}pt;
                }}
            """)
    
    def _save_logs(self) -> None:
        """Save logs to file."""
        if not self._console_panel:
            return
        
        # Get logs text
        logs_text = self._console_panel.get_logs_text()
        
        if not logs_text:
            # Use toast notification instead of blocking dialog
            if not self._toast_manager:
                from src.views.toast_notification import get_toast_manager
                self._toast_manager = get_toast_manager(self)
            
            self._toast_manager.show_info(
                tr("no_logs_to_save", "No logs to save")
            )
            return
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = tr("logs_default_filename", "uart_logs_{timestamp}.txt").format(
            timestamp=timestamp
        )
        
        # Show save dialog
        file_filter = tr(
            "text_files_filter",
            "Text Files (*.txt);;All Files (*)",
        )

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            tr("save_logs", "Save Logs"),
            default_name,
            file_filter,
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(logs_text)
                
                self.statusBar().showMessage(
                    tr("logs_saved", "Logs saved to {path}").format(path=file_path),
                    3000
                )
            except Exception as e:
                # Use toast notification instead of blocking dialog
                if not self._toast_manager:
                    from src.views.toast_notification import get_toast_manager
                    self._toast_manager = get_toast_manager(self)
                
                self._toast_manager.show_error(
                    tr("save_error", "Failed to save logs: {error}").format(error=str(e))
                )
    
    def _update_icons_on_theme_change(self) -> None:
        """Update all theme-aware icons when theme changes."""
        # Update history button icon
        if hasattr(self, '_btn_open_history'):
            self._btn_open_history.setIcon(get_icon("clock-rotate-left"))
            self._btn_open_history.update()
    
    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self.statusBar().showMessage(
            tr("status_theme_changed", "Theme: {theme}").format(theme=theme),
            2000
        )
        # Update icons for theme-aware widgets
        self._update_icons_on_theme_change()
        # Process events to ensure icons are updated
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        # Re-apply theme-specific properties to the whole widget tree
        self._apply_theme_to_hierarchy()
        # Re-apply Windows 11 visual effects (Mica, corner radius)
        self._apply_windows11_effects()
    
    def _on_language_changed(self, language: str) -> None:
        """Handle language change."""
        # Update window title
        self.setWindowTitle(tr("app_name", "UART Control"))
        
        # Update static texts
        port_ids = [
            (1, "cpu1"),
            (2, "cpu2"),
            (3, "tlm"),
        ]

        for port_num, port_key in port_ids:
            if port_num in self._port_viewmodels:
                new_label = tr(port_key, port_key.upper())
                self._port_viewmodels[port_num].set_port_label(new_label)
                self._port_views[port_num].setTitle(new_label)

        self._setup_menu()

        for row, (port_num, port_key) in enumerate(zip([1, 2, 3], self._counter_ports)):
            port_name = tr(port_key, port_key.upper())
            label_text = tr("port_label_template", "{name}:").format(name=port_name)
            label_widget = self._counter_label_widgets[row]
            label_widget.setText(label_text)

            rx_label = self._counter_labels[f"{port_key}_rx"]
            tx_label = self._counter_labels[f"{port_key}_tx"]
            error_label = self._counter_labels[f"{port_key}_error"]
            time_label = self._counter_labels[f"{port_key}_time"]
            
            rx_label.setText(
                tr("rx_label", "RX: {count}").format(
                    count=self._port_viewmodels[port_num].rx_count
                )
            )
            tx_label.setText(
                tr("tx_label", "TX: {count}").format(
                    count=self._port_viewmodels[port_num].tx_count
                )
            )
            if error_label:
                error_label.setText(
                    tr("error_label", "Errors: {count}").format(
                        count=self._port_viewmodels[port_num].error_count
                    )
                )
            if time_label:
                conn_time = self._port_viewmodels[port_num].connection_time
                time_label.setText(
                    tr("time_label", "Time: {time}s").format(
                        time=int(conn_time)
                    )
                )

        self._lbl_history_title.setText(tr("command_history", "Command History"))
        self._btn_open_history.setText(tr("history_open", "History"))
        self._update_history_summary()
        self._command_group.setTitle(tr("data_transmission", "Data Transmission"))
        self._le_command.setPlaceholderText(tr("enter_command", "Enter command..."))
        self._btn_combo.setText(tr("send_to_both", "1+2"))
        self._btn_cpu1.setText(tr("send_to_cpu1", "CPU1"))
        self._btn_cpu2.setText(tr("send_to_cpu2", "CPU2"))
        self._btn_tlm.setText(tr("send_to_tlm", "TLM"))

        current_lang = translator.get_language()
        for lang, action in self._language_actions.items():
            action.setChecked(lang == current_lang)

        # Update status
        self.statusBar().showMessage(
            tr("language_changed", "Language changed to {lang}").format(lang=language),
            2000
        )
        # Language change can recreate menus/toolbars – re-apply theme to hierarchy
        self._apply_theme_to_hierarchy()
        
        # Update language button if exists
        if hasattr(self, '_lang_btn'):
            self._lang_btn.setText(language.upper())
    
    def _toggle_language(self) -> None:
        """Toggle between available languages."""
        current = translator.get_language()
        new_lang = "ru_RU" if current == "en_US" else "en_US"
        translator.set_language(new_lang)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle close event - shutdown all ports."""
        # Flush command history to disk before shutting down
        try:
            if hasattr(self, "_history_model") and self._history_model is not None:
                self._history_model.flush()
        except Exception:
            # Закрытие окна не должно срываться из‑за ошибок записи истории
            pass
        
        # Cleanup global hotkeys
        if hasattr(self, '_hotkey_manager') and self._hotkey_manager:
            self._hotkey_manager.cleanup()
        
        # Shutdown all port ViewModels
        for viewmodel in self._port_viewmodels.values():
            viewmodel.shutdown()
        
        # Give threads time to finish
        self._wait_for_threads()
        
        event.accept()
    
    def _wait_for_threads(self, timeout_ms: int = 2000) -> None:
        """Wait for all worker threads to finish."""
        import time
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000.0
        
        for viewmodel in self._port_viewmodels.values():
            if hasattr(viewmodel, '_worker_thread') and viewmodel._worker_thread:
                thread = viewmodel._worker_thread
                if thread.isRunning():
                    remaining = timeout_seconds - (time.time() - start_time)
                    if remaining > 0:
                        thread.wait(int(remaining * 1000))

    def _register_button(
        self,
        button: QtWidgets.QPushButton,
        class_name: Optional[str] = None,
    ) -> None:
        if class_name:
            existing = button.property("class")
            if existing:
                classes = set(str(existing).split())
                classes.add(class_name)
                button.setProperty("class", " ".join(sorted(classes)))
            else:
                button.setProperty("class", class_name)
        if button not in self._themed_buttons:
            self._themed_buttons.append(button)
        self._apply_theme_to_button(button)

    def _apply_theme_to_buttons(self) -> None:
        for button in self._themed_buttons:
            self._apply_theme_to_button(button)

    def _apply_theme_to_button(self, button: QtWidgets.QPushButton) -> None:
        theme_class = "light" if theme_manager.is_light_theme() else "dark"
        button.setProperty("themeClass", theme_class)
        self._refresh_widget_style(button)

    @staticmethod
    def _refresh_widget_style(widget: QtWidgets.QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _apply_theme_to_hierarchy(self) -> None:
        """
        OPTIMIZED: No longer needed with palette-based QSS.
        
        The new QSS uses palette() function which automatically inherits
        from QApplication palette. No need to set themeClass on each widget.
        
        This dramatically improves theme switching performance from O(n) 
        to O(1) where n = number of widgets.
        """
        # With palette-based QSS, theme changes automatically propagate
        # through Qt's style system. No manual iteration needed!
        pass
    
    def _apply_windows11_effects(self) -> None:
        """
        Apply Windows 11 visual effects: rounded corners, Mica backdrop.
        This is called on startup and when theme changes.
        """
        # Only apply on Windows
        if platform.system() != "Windows":
            return
        
        # Get window handle
        hwnd = int(self.winId())
        if not hwnd:
            return
        
        # Apply Windows 11 visual style
        is_dark = theme_manager.is_dark_theme()
        apply_windows_11_style(hwnd, is_dark)
    
    def _setup_global_hotkeys(self) -> None:
        """
        Setup global system-wide hotkeys (Windows only).
        These work even when the app is not in focus.
        """
        # Only setup on Windows
        if platform.system() != "Windows":
            return
        
        # Initialize hotkey manager
        hwnd = int(self.winId())
        if not hwnd:
            return
        
        try:
            self._hotkey_manager = GlobalHotkeyManager(hwnd)
            
            # Register global hotkeys
            # Ctrl+Alt+S - Show/Hide window
            self._hotkey_manager.register_hotkey(
                VK.S, MOD_CONTROL | MOD_ALT,
                self._toggle_window_visibility
            )
            
            # Ctrl+Alt+1 - Send to CPU1
            self._hotkey_manager.register_hotkey(
                VK.NUM1, MOD_CONTROL | MOD_ALT,
                lambda: self._send_command(1)
            )
            
            # Ctrl+Alt+2 - Send to CPU2
            self._hotkey_manager.register_hotkey(
                VK.NUM2, MOD_CONTROL | MOD_ALT,
                lambda: self._send_command(2)
            )
            
            # Install native event filter to handle hotkey messages
            from PySide6.QtCore import QAbstractNativeEventFilter
            self._hotkey_event_filter = _GlobalHotkeyEventFilter(self._hotkey_manager)
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.instance().installNativeEventFilter(self._hotkey_event_filter)
            
        except Exception as e:
            # Hotkeys are non-critical, just log and continue
            print(f"Failed to setup global hotkeys: {e}")
            self._hotkey_manager = None
    
    def _toggle_window_visibility(self) -> None:
        """Toggle window visibility (show/hide)."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
