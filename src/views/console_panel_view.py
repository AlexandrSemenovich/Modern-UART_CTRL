"""
ConsolePanelView: UI component for displaying serial console logs.
Reusable widget for showing RX/TX data from multiple ports.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Signal, Qt, QTimer
from typing import Optional, Dict, List, Callable
import html

from src.utils.translator import tr, translator
from src.styles.constants import Fonts, Sizes
from src.utils.config_loader import config_loader
from src.utils.theme_manager import theme_manager
import html


class LogWidget:
    """Container for log widget and its label."""
    def __init__(self):
        self.label: Optional[QtWidgets.QLabel] = None
        self.text_edit: Optional[QtWidgets.QTextEdit] = None


class ConsolePanelView(QtWidgets.QWidget):
    """
    UI component for displaying console logs from serial ports.
    
    Features:
    - Multiple log panels (CPU1, CPU2, TLM, Combined)
    - Search functionality
    - Clear and save operations
    - Timestamps and source labels
    - Auto-scroll to bottom
    
    Signals:
        search_changed (str): Search text changed
        clear_requested (): Clear all logs requested
        save_requested (): Save logs requested
    """
    
    search_changed = Signal(str)
    clear_requested = Signal()
    save_requested = Signal()
    
    def __init__(
        self, 
        parent: Optional[QtWidgets.QWidget] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize ConsolePanelView.
        
        Args:
            parent: Parent widget
            config: Optional configuration dictionary
        """
        super().__init__(parent)
        
        self._config = config or {}
        self._port_labels: List[str] = ['CPU1', 'CPU2', 'TLM']
        self._log_widgets: Dict[str, LogWidget] = {}
        self._log_cache: Dict[str, List[str]] = {}
        self._max_lines: int = self._config.get('max_lines', 10000)
        
        # Display options
        self._show_time: bool = True
        self._show_source: bool = True
        
        # Search filter
        self._search_text: str = ""
        
        self._themed_buttons: List[QtWidgets.QPushButton] = []
        self._setup_ui()
        translator.language_changed.connect(self.retranslate_ui)
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._colors = config_loader.get_colors(self._current_theme())
    
    def _setup_ui(self) -> None:
        """Create and arrange UI elements."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # Tab widget for different log views
        self._tab_widget = QtWidgets.QTabWidget()
        self._tab_widget.setObjectName("console_tabs")
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(False)
        
        # Create tabs for each port
        self._create_log_tabs()
        
        layout.addWidget(self._tab_widget, 1)
        
        self.setLayout(layout)

    def _create_toolbar(self) -> QtWidgets.QHBoxLayout:
        """Create toolbar with search and action buttons."""
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(Sizes.TOOLBAR_SPACING)
        toolbar.setContentsMargins(
            Sizes.TOOLBAR_MARGIN, Sizes.TOOLBAR_MARGIN,
            Sizes.TOOLBAR_MARGIN, Sizes.TOOLBAR_MARGIN
        )
        
        # Search field
        self._search_label = QtWidgets.QLabel(tr("search", "Search:"))
        toolbar.addWidget(self._search_label)

        self._search_edit = QtWidgets.QLineEdit()
        self._search_edit.setPlaceholderText(tr("search_logs", "Search logs..."))
        self._search_edit.setMaximumWidth(Sizes.SEARCH_FIELD_MAX_WIDTH)
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit)
        
        # Display options
        self._show_label = QtWidgets.QLabel(tr("show", "Show:"))
        toolbar.addWidget(self._show_label)

        self._chk_time = QtWidgets.QCheckBox(tr("time", "Time"))
        self._chk_time.setChecked(True)
        self._chk_time.stateChanged.connect(self._on_display_option_changed)
        toolbar.addWidget(self._chk_time)
        
        self._chk_source = QtWidgets.QCheckBox(tr("source", "Source"))
        self._chk_source.setChecked(True)
        self._chk_source.stateChanged.connect(self._on_display_option_changed)
        toolbar.addWidget(self._chk_source)
        
        toolbar.addStretch()
        
        # Action buttons
        self._btn_clear = QtWidgets.QPushButton(tr("clear", "Clear"))
        self._btn_clear.setMaximumWidth(Sizes.BUTTON_CLEAR_MAX_WIDTH)
        self._register_button(self._btn_clear, "danger")
        self._btn_clear.clicked.connect(self.clear_requested.emit)
        toolbar.addWidget(self._btn_clear)

        self._btn_save = QtWidgets.QPushButton(tr("save", "Save"))
        self._btn_save.setMaximumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH)
        self._register_button(self._btn_save, "primary")
        self._btn_save.clicked.connect(self.save_requested.emit)
        toolbar.addWidget(self._btn_save)
        
        return toolbar
    
    def _create_log_tabs(self) -> None:
        """Create log tabs for each port and combined view."""
        
        # Combined tab (CPU1 + CPU2)
        combined_widget = self._create_combined_widget()
        self._tab_widget.addTab(combined_widget, tr("combined", "1+2"))
        
        # Individual tabs
        for port_label in self._port_labels:
            tab_widget = self._create_single_log_widget(port_label)
            self._tab_widget.addTab(tab_widget, tr(port_label.lower(), port_label))
    
    def _create_combined_widget(self) -> QtWidgets.QWidget:
        """Create combined view with CPU1 and CPU2 side by side."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # CPU1 column
        cpu1_layout = QtWidgets.QVBoxLayout()
        cpu1_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        
        cpu1_label = QtWidgets.QLabel(tr("send_to_cpu1", "CPU1"))
        cpu1_layout.addWidget(cpu1_label, 0)
        
        cpu1_log = self._create_log_edit()
        cpu1_layout.addWidget(cpu1_log, 1)
        
        layout.addLayout(cpu1_layout, 1)
        
        # CPU2 column
        cpu2_layout = QtWidgets.QVBoxLayout()
        cpu2_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        
        cpu2_label = QtWidgets.QLabel(tr("send_to_cpu2", "CPU2"))
        cpu2_layout.addWidget(cpu2_label, 0)
        
        cpu2_log = self._create_log_edit()
        cpu2_layout.addWidget(cpu2_log, 1)
        
        layout.addLayout(cpu2_layout, 1)
        
        return widget
    
    def _create_single_log_widget(self, port_label: str) -> QtWidgets.QWidget:
        """Create a single log widget for one port."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        
        # Header
        header = self._create_tab_header(port_label)
        layout.addWidget(header)
        
        # Log text edit
        log_edit = self._create_log_edit()
        layout.addWidget(log_edit, 1)
        
        # Store reference
        log_widget = LogWidget()
        log_widget.label = header
        log_widget.text_edit = log_edit
        self._log_widgets[port_label] = log_widget
        
        # Initialize cache for this port
        self._log_cache[port_label] = []
        
        return widget
    
    def _create_log_edit(self) -> QtWidgets.QTextEdit:
        """Create a read-only log text edit widget."""
        edit = QtWidgets.QTextEdit()
        edit.setReadOnly(True)
        edit.setFont(Fonts.get_monospace_font())
        edit.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        edit.setUndoRedoEnabled(False)
        return edit
    
    def _create_tab_header(self, port_label: str) -> QtWidgets.QLabel:
        """Create header label for a log tab."""
        label = QtWidgets.QLabel(port_label)
        return label
    
    def append_log(self, port_label: str, html_content: str, plain_text: str) -> None:
        """
        Append log content to a specific port's log.
        
        Args:
            port_label: Port identifier (CPU1, CPU2, TLM)
            html_content: HTML formatted content
            plain_text: Plain text version
        """
        # Add to cache
        if port_label not in self._log_cache:
            self._log_cache[port_label] = []
        
        self._log_cache[port_label].append((html_content, plain_text))
        
        # Limit cache size
        max_cache = self._max_lines * 2  # HTML + plain pairs
        if len(self._log_cache[port_label]) > max_cache:
            self._log_cache[port_label] = self._log_cache[port_label][-max_cache:]
        
        # Get widget
        if port_label in self._log_widgets:
            widget = self._log_widgets[port_label]
            if widget.text_edit:
                widget.text_edit.append(html_content)
    
    def append_rx(self, port_label: str, data: str) -> None:
        """
        Append received data to log.
        
        Args:
            port_label: Port identifier
            data: Received data
        """
        formatted = self._format_rx(port_label, data)
        self.append_log(port_label, formatted, data)
    
    def append_tx(self, port_label: str, data: str) -> None:
        """
        Append transmitted data to log.
        
        Args:
            port_label: Port identifier
            data: Sent data
        """
        formatted = self._format_tx(port_label, data)
        self.append_log(port_label, formatted, data)
    
    def append_system(self, port_label: str, message: str) -> None:
        """
        Append system message to log.
        
        Args:
            port_label: Port identifier
            message: System message
        """
        formatted = self._format_system(port_label, message)
        self.append_log(port_label, formatted, message)
    
    def _format_rx(self, port_label: str, data: str) -> str:
        """Format received data for display."""
        return self._format_message(port_label, data, "RX")
    
    def _format_tx(self, port_label: str, data: str) -> str:
        """Format transmitted data for display."""
        return self._format_message(port_label, data, "TX")
    
    def _format_system(self, port_label: str, message: str) -> str:
        """Format system message for display."""
        return self._format_message(port_label, message, "SYS")
    
    def _format_message(
        self, 
        port_label: str, 
        text: str, 
        msg_type: str
    ) -> str:
        """
        Format a message for log display.
        
        Args:
            port_label: Port identifier
            text: Message text
            msg_type: Message type (RX, TX, SYS)
            color: CSS color for text
            
        Returns:
            HTML formatted string
        """
        if not text or not text.strip():
            return ""
        
        # Remove trailing line endings
        text = text.rstrip('\r\n')
        
        parts = []
        colors = self._colors
        timestamp = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        if self._show_time:
            parts.append(f"<span style='color:{colors.timestamp}'>[{timestamp}]</span> ")
        
        if self._show_source:
            label_color = {
                "RX": colors.rx_label,
                "TX": colors.tx_label,
                "SYS": colors.sys_label,
            }.get(msg_type, colors.sys_label)
            parts.append(f"<b style='color:{label_color}'>{msg_type}({port_label}):</b> ")
        
        body_color = {
            "RX": colors.rx_text,
            "TX": colors.tx_text,
            "SYS": colors.sys_text,
        }.get(msg_type, colors.sys_text)
        parts.append(f"<span style='color:{body_color}; white-space:pre'>{html.escape(text)}</span>")
        return "".join(parts)

    def _current_theme(self) -> str:
        return "light" if theme_manager.is_light_theme() else "dark"

    def _on_theme_changed(self, theme: str) -> None:
        self._colors = config_loader.get_colors(theme)
        self._apply_theme_to_buttons()
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._search_text = text
        self.search_changed.emit(text)
    
    def _on_display_option_changed(self) -> None:
        """Handle display option change."""
        self._show_time = self._chk_time.isChecked()
        self._show_source = self._chk_source.isChecked()
    
    def clear_all(self) -> None:
        """Clear all logs."""
        for port_label, widget in self._log_widgets.items():
            if widget.text_edit:
                widget.text_edit.clear()
        
        self._log_cache.clear()
        self.clear_requested.emit()
    
    def save_logs(self) -> None:
        """Request to save logs."""
        self.save_requested.emit()
    
    def get_logs_text(self, port_label: Optional[str] = None) -> str:
        """
        Get logs as plain text.
        
        Args:
            port_label: Specific port label or None for all
            
        Returns:
            Plain text of logs
        """
        if port_label and port_label in self._log_cache:
            lines = [plain for _, plain in self._log_cache[port_label]]
            return "".join(lines)
        elif not port_label:
            all_lines = []
            for port_cache in self._log_cache.values():
                all_lines.extend([plain for _, plain in port_cache])
            return "".join(all_lines)
        return ""
    
    def get_log_count(self, port_label: Optional[str] = None) -> int:
        """Get number of log lines."""
        if port_label and port_label in self._log_cache:
            return len(self._log_cache[port_label])
        elif not port_label:
            return sum(len(cache) for cache in self._log_cache.values())
        return 0
    
    def scroll_to_bottom(self, port_label: Optional[str] = None) -> None:
        """Scroll log to bottom."""
        if port_label and port_label in self._log_widgets:
            widget = self._log_widgets[port_label]
            if widget.text_edit:
                widget.text_edit.verticalScrollBar().setValue(
                    widget.text_edit.verticalScrollBar().maximum()
                )
        elif not port_label:
            # Scroll current tab
            current_index = self._tab_widget.currentIndex()
            if current_index >= 0:
                tab = self._tab_widget.widget(current_index)
                # Find text edit in tab
                self._scroll_widget_to_bottom(tab)
    
    def _scroll_widget_to_bottom(self, widget: QtWidgets.QWidget) -> None:
        """Recursively find and scroll text edit to bottom."""
        for child in widget.findChildren(QtWidgets.QTextEdit):
            child.verticalScrollBar().setValue(child.verticalScrollBar().maximum())
    
    @property
    def show_time(self) -> bool:
        """Get show time option."""
        return self._show_time
    
    @property
    def show_source(self) -> bool:
        """Get show source option."""
        return self._show_source
    
    @property
    def search_text(self) -> str:
        """Get current search text."""
        return self._search_text
    def retranslate_ui(self) -> None:
        """Update toolbar labels and buttons on language change."""
        self._search_label.setText(tr("search", "Search:"))
        self._search_edit.setPlaceholderText(tr("search_logs", "Search logs..."))
        self._show_label.setText(tr("show", "Show:"))
        self._chk_time.setText(tr("time", "Time"))
        self._chk_source.setText(tr("source", "Source"))
        self._btn_clear.setText(tr("clear", "Clear"))
        self._btn_save.setText(tr("save", "Save"))
        self._apply_theme_to_buttons()

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
        if not hasattr(self, "_themed_buttons"):
            self._themed_buttons = []
        if button not in self._themed_buttons:
            self._themed_buttons.append(button)
        self._apply_theme_to_button(button)

    def _apply_theme_to_buttons(self) -> None:
        for button in getattr(self, "_themed_buttons", []):
            self._apply_theme_to_button(button)

    def _apply_theme_to_button(self, button: QtWidgets.QPushButton) -> None:
        theme_class = "light" if theme_manager.is_light_theme() else "dark"
        button.setProperty("themeClass", theme_class)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()
