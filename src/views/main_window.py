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
from PySide6.QtGui import QIcon, QFont, QColor, QKeySequence, QShortcut, QActionGroup
from typing import Dict, Optional, List
import os
import sys
import time
import datetime

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
from src.utils.translator import translator, tr
from src.styles.constants import Fonts, Sizes, SerialConfig
from src.views.port_panel_view import PortPanelView
from src.views.console_panel_view import ConsolePanelView
from src.viewmodels.com_port_viewmodel import ComPortViewModel, PortConnectionState
from src.viewmodels.command_history_viewmodel import CommandHistoryModel
from src.views.command_history_dialog import CommandHistoryDialog


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
        
        # Command history
        self._history_model = CommandHistoryModel(self)
        self._history_dialog: Optional[CommandHistoryDialog] = None
        
        # Setup window properties
        self._setup_window()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        
        # Connect theme changes
        theme_manager.theme_changed.connect(self._on_theme_changed)
        # Тема уже применена в main.py, не применяем повторно
        
        # Connect language changes
        translator.language_changed.connect(self._on_language_changed)
        
        # Status bar
        self.statusBar().showMessage(tr("ready", "Ready"))
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(tr("app_name", "UART Control"))
        self.setGeometry(100, 100, Sizes.WINDOW_DEFAULT_WIDTH, Sizes.WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        self._set_window_icon()
        
        # Настройка кастомного title bar через Windows API (если доступно)
        self._setup_custom_title_bar()
    
    def _set_window_icon(self) -> None:
        """Set window icon from assets."""
        icon_paths = [
            "assets/icons/icon_black.ico",
            "assets/icons/icon_white.ico",
        ]
        
        for path in icon_paths:
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                path
            )
            if os.path.exists(full_path):
                self.setWindowIcon(QIcon(full_path))
                break
    
    def _setup_custom_title_bar(self) -> None:
        """Настройка кастомного title bar для Windows 11+ через DWM API."""
        if not HAS_WIN32_API:
            return
        
        try:
            # Windows API константы
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            # Получаем HWND окна (после показа окна)
            def apply_title_bar_theme():
                try:
                    hwnd = int(self.winId())
                    if hwnd:
                        # Включаем тёмный режим для title bar
                        value = ctypes.c_int(1 if theme_manager.is_dark_theme() else 0)
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            wintypes.HWND(hwnd),
                            DWMWA_USE_IMMERSIVE_DARK_MODE,
                            ctypes.byref(value),
                            ctypes.sizeof(value)
                        )
                        
                        # Пытаемся установить цвет caption (Windows 11 22H2+)
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
        right_panel = self._create_right_panel()
        right_panel.setMinimumWidth(Sizes.RIGHT_PANEL_MIN_WIDTH)
        right_panel.setMaximumWidth(Sizes.RIGHT_PANEL_MAX_WIDTH)
        right_panel.setObjectName("right_panel")
        hsplit.addWidget(right_panel)
        
        # Set stretch factors
        hsplit.setStretchFactor(0, 0)  # Left - fixed
        hsplit.setStretchFactor(1, 1)  # Center - expandable
        hsplit.setStretchFactor(2, 0)  # Right - fixed
        
        main_layout.addWidget(hsplit)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Apply current theme classes to all widgets in the hierarchy
        self._apply_theme_to_hierarchy()
        
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
            
            # Connect ViewModel signals to console
            viewmodel.data_received.connect(
                lambda data, key=port_key: self._console_panel.append_rx(
                    tr(key, key.upper()), data
                )
            )
            viewmodel.data_sent.connect(
                lambda data, key=port_key: self._console_panel.append_tx(
                    tr(key, key.upper()), data
                )
            )
            viewmodel.error_occurred.connect(
                lambda msg, key=port_key, vm=viewmodel: self._handle_port_error(
                    tr(key, key.upper()), vm, msg
                )
            )
            viewmodel.state_changed.connect(
                lambda state, num=port_num: self._on_port_state_changed(num, state)
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
        self._register_button(self._btn_combo, "primary")
        self._btn_combo.setProperty("semanticRole", "command_combo")
        self._btn_combo.clicked.connect(lambda: self._send_command(0))
        buttons_layout.addWidget(self._btn_combo, 0, 0)

        # CPU1 button
        self._btn_cpu1 = QtWidgets.QPushButton(tr("send_to_cpu1", "CPU1"))
        self._btn_cpu1.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)
        self._btn_cpu1.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
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
        self._btn_open_history.setIcon(QIcon("assets/icons/fa/clock-rotate-left.svg"))
        self._btn_open_history.setText(tr("history_open", "History"))
        self._btn_open_history.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
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
        
        # Counters group
        counters_grp = QtWidgets.QGroupBox(tr("port_counters", "Port Counters"))
        counters_layout = QtWidgets.QGridLayout()
        counters_layout.setSpacing(Sizes.LAYOUT_SPACING)
        counters_layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Counter labels
        self._counter_labels: Dict[str, QtWidgets.QLabel] = {}
        
        self._counter_ports = ["cpu1", "cpu2", "tlm"]

        self._counter_label_widgets: List[QtWidgets.QLabel] = []

        for row, port_key in enumerate(self._counter_ports):
            port_name = tr(port_key, port_key.upper())
            label_widget = QtWidgets.QLabel(
                tr("port_label_template", "{name}:").format(name=port_name)
            )
            label_widget.setProperty("translation_key", port_key)
            self._counter_label_widgets.append(label_widget)
            counters_layout.addWidget(label_widget, row, 0)
            
            rx_label = QtWidgets.QLabel(
                tr("rx_label", "RX: {count}").format(count=0)
            )
            tx_label = QtWidgets.QLabel(
                tr("tx_label", "TX: {count}").format(count=0)
            )
            
            counters_layout.addWidget(rx_label, row, 1)
            counters_layout.addWidget(tx_label, row, 2)
            
            self._counter_labels[f"{port_key}_rx"] = rx_label
            self._counter_labels[f"{port_key}_tx"] = tx_label
        
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

    # Maximum number of error dialogs to keep
    _MAX_ERROR_DIALOGS = 5
    
    def _handle_port_error(self, port_label: str, viewmodel: ComPortViewModel, message: str) -> None:
        plain_msg = message
        if '<' in message:
            import re
            plain_msg = re.sub('<.*?>', '', message)
        if self._console_panel:
            self._console_panel.append_system(port_label, plain_msg)
        
        # Limit number of dialogs to prevent memory leaks
        if len(self._error_dialogs) >= self._MAX_ERROR_DIALOGS:
            # Close oldest dialog
            oldest = self._error_dialogs.pop(0)
            oldest.close()
            oldest.deleteLater()
        
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Critical,
            tr("error", "Error"),
            plain_msg,
            parent=self,
        )
        dialog.setWindowTitle(tr("error", "Error"))
        
        # Auto-cleanup when dialog is closed
        dialog.finished.connect(lambda _: self._cleanup_error_dialog(dialog))
        dialog.show()
        self._error_dialogs.append(dialog)
    
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
    
    def _send_command(self, port_num: int) -> None:
        """
        Send command to specified port(s).
        
        Args:
            port_num: Port number (0=all, 1=CPU1, 2=CPU2, 3=TLM)
        """
        command = self._le_command.text()
        if not command:
            return
        
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
        """Clear all console logs."""
        if self._console_panel:
            self._console_panel.clear_all()
    
    def _save_logs(self) -> None:
        """Save logs to file."""
        if not self._console_panel:
            return
        
        # Get logs text
        logs_text = self._console_panel.get_logs_text()
        
        if not logs_text:
            QtWidgets.QMessageBox.information(
                self,
                tr("info", "Info"),
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
                QtWidgets.QMessageBox.critical(
                    self,
                    tr("error", "Error"),
                    tr("save_error", "Failed to save logs: {error}").format(error=e)
                )
    
    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self.statusBar().showMessage(
            tr("theme_changed", "Theme changed to {theme}").format(theme=theme),
            2000
        )
        # Re-apply theme-specific properties to the whole widget tree
        self._apply_theme_to_hierarchy()
    
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
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle close event - shutdown all ports."""
        # Flush command history to disk before shutting down
        try:
            if hasattr(self, "_history_model") and self._history_model is not None:
                self._history_model.flush()
        except Exception:
            # Закрытие окна не должно срываться из‑за ошибок записи истории
            pass

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
        Apply current themeClass property to all widgets in the window.

        This makes QSS selectors like QWidget[themeClass=\"dark\"] /
        QLineEdit[themeClass=\"light\"] work consistently across the UI,
        not только для вручную зарегистрированных кнопок.
        """
        theme_class = "light" if theme_manager.is_light_theme() else "dark"

        # Include the window itself and all child widgets
        widgets: list[QtWidgets.QWidget] = [self]
        widgets.extend(self.findChildren(QtWidgets.QWidget))

        for w in widgets:
            w.setProperty("themeClass", theme_class)
            self._refresh_widget_style(w)
        
        # Специально применяем к панелям для правильного отображения границ
        if hasattr(self, '_console_panel') and self._console_panel:
            self._console_panel.setProperty("themeClass", theme_class)
            self._refresh_widget_style(self._console_panel)
