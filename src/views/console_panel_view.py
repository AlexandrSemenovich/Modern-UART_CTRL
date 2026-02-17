"""
ConsolePanelView: UI component for displaying serial console logs.
Reusable widget for showing RX/TX data from multiple ports.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Signal, Qt, QTimer
from typing import Optional, Dict, List, Callable
from collections import deque
import html
import re

from src.utils.translator import tr, translator
from src.styles.constants import Fonts, Sizes, ConsoleLimits
from src.utils.config_loader import config_loader
from src.utils.theme_manager import theme_manager


class LogWidget:
    """Container for log widget and its label."""
    def __init__(self):
        self.label: Optional[QtWidgets.QLabel] = None
        self.text_edit: Optional[QtWidgets.QTextEdit] = None


class DropableTextEdit(QtWidgets.QTextEdit):
    """QTextEdit with drag-and-drop support for text files."""
    
    file_dropped = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if any URLs are text files
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.endswith(('.txt', '.log', '.hex', '.bin', '.csv')):
                        event.acceptProposedAction()
                        return
        elif event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Handle drag move event."""
        event.acceptProposedAction()
    
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handle drop event - emit file path or text."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.endswith(('.txt', '.log', '.hex', '.bin', '.csv')):
                        self.file_dropped.emit(file_path)
                        event.acceptProposedAction()
                        return
        elif event.mimeData().hasText():
            # Emit the dropped text
            self.file_dropped.emit(event.mimeData().text())
            event.acceptProposedAction()


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
    file_dropped = Signal(str)  # Signal for file drop - emits file path
    
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
        self._combined_log_widgets: Dict[str, QtWidgets.QTextEdit] = {}
        # Use deque with maxlen for O(1) cache operations
        self._log_cache: Dict[str, deque] = {}
        # Максимальное количество строк в кэше для одного порта
        from src.styles.constants import ConsoleLimits as _ConsoleLimits  # локальный импорт для избежания циклов
        self._max_lines: int = int(self._config.get('max_lines', _ConsoleLimits.MAX_CACHE_LINES))
        
        # Display options
        self._show_time: bool = True
        self._show_source: bool = True
        
        # Search filter
        self._search_text: str = ""
        
        # Throttled update state
        self._pending_updates: Dict[str, List[tuple]] = {}
        self._update_timer: Optional[QTimer] = None
        self._update_interval_ms: int = 50  # Batch updates every 50ms
        
        # Search debounce timer (300ms)
        self._search_timer: Optional[QTimer] = None
        self._search_debounce_ms: int = 300
        
        self._themed_buttons: List[QtWidgets.QPushButton] = []
        self._setup_ui()
        translator.language_changed.connect(self.retranslate_ui)
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._colors = config_loader.get_colors(self._current_theme())
        self._init_update_timer()
    
    def _setup_ui(self) -> None:
        """Create and arrange UI elements."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(Sizes.LAYOUT_SPACING)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN
        )
        
        # Toolbar в отдельном контейнере для стилизации
        self._toolbar_container = QtWidgets.QWidget()
        self._toolbar_container.setObjectName("console_toolbar_container")
        self._toolbar_container.setMinimumHeight(50)  # Минимальная высота для правильного центрирования
        self._toolbar_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        
        # Устанавливаем themeClass на основе эффективной темы для согласованного применения стилей
        effective_theme = theme_manager._get_effective_theme()
        theme_class = "light" if effective_theme == "light" else "dark"
        self._toolbar_container.setProperty("themeClass", theme_class)
        
        toolbar_layout = QtWidgets.QVBoxLayout(self._toolbar_container)
        toolbar_layout.setContentsMargins(10, 0, 10, 8)
        toolbar_layout.setSpacing(0)
        
        # Создаем виджет-обертку для toolbar layout
        toolbar_widget = QtWidgets.QWidget()
        toolbar_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        toolbar_widget.setMinimumHeight(Sizes.INPUT_MIN_HEIGHT)

        toolbar = self._create_toolbar()
        toolbar_widget.setLayout(toolbar)
        
        # Добавляем toolbar widget с центрированием по вертикали без лишних отступов
        toolbar_layout.addWidget(toolbar_widget, 0, Qt.AlignVCenter)
        
        layout.addWidget(self._toolbar_container)
        
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
        toolbar.setContentsMargins(0, 0, 0, 0)  # отступы задаются контейнером
        toolbar.setAlignment(Qt.AlignVCenter)  # центрирование только по вертикали
        control_height = Sizes.INPUT_MIN_HEIGHT
        
        # Search field
        self._search_label = QtWidgets.QLabel(tr("search", "Search:"))
        self._search_label.setAlignment(Qt.AlignVCenter)
        self._search_label.setFixedHeight(control_height)
        toolbar.addWidget(self._search_label, 0, Qt.AlignVCenter)

        self._search_edit = QtWidgets.QLineEdit()
        self._search_edit.setPlaceholderText(tr("search_logs", "Search logs..."))
        self._search_edit.setMaximumWidth(Sizes.SEARCH_FIELD_MAX_WIDTH)
        self._search_edit.setFixedHeight(control_height)
        self._search_edit.setAccessibleName(tr("search_a11y", "Search logs"))
        self._search_edit.setAccessibleDescription(tr("search_desc_a11y", "Enter text to filter log messages"))
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit, 0, Qt.AlignVCenter)
        
        # Display options
        self._show_label = QtWidgets.QLabel(tr("show", "Show:"))
        self._show_label.setAlignment(Qt.AlignVCenter)
        self._show_label.setFixedHeight(control_height)
        toolbar.addWidget(self._show_label, 0, Qt.AlignVCenter)

        self._chk_time = QtWidgets.QCheckBox(tr("time", "Time"))
        self._chk_time.setChecked(True)
        self._chk_time.setFixedHeight(control_height)
        self._chk_time.setAccessibleName(tr("chk_time_a11y", "Show timestamp"))
        self._chk_time.setAccessibleDescription(tr("chk_time_desc_a11y", "Toggle display of timestamp in log messages"))
        self._chk_time.stateChanged.connect(self._on_display_option_changed)
        toolbar.addWidget(self._chk_time, 0, Qt.AlignVCenter)

        self._chk_source = QtWidgets.QCheckBox(tr("source", "Source"))
        self._chk_source.setChecked(False)
        self._chk_source.setFixedHeight(control_height)
        self._chk_source.setAccessibleName(tr("chk_source_a11y", "Show source"))
        self._chk_source.setAccessibleDescription(tr("chk_source_desc_a11y", "Toggle display of message source in log messages"))
        self._chk_source.stateChanged.connect(self._on_display_option_changed)
        toolbar.addWidget(self._chk_source, 0, Qt.AlignVCenter)
        
        toolbar.addStretch()
        
        # Action buttons - компактные для toolbar
        self._btn_clear = QtWidgets.QPushButton(tr("clear", "Clear"))
        self._btn_clear.setMaximumWidth(Sizes.BUTTON_CLEAR_MAX_WIDTH)
        self._btn_clear.setFixedHeight(control_height)
        self._btn_clear.setAccessibleName(tr("btn_clear_a11y", "Clear logs"))
        self._btn_clear.setAccessibleDescription(tr("btn_clear_desc_a11y", "Click to clear all log messages"))
        self._register_button(self._btn_clear, "danger")
        self._btn_clear.clicked.connect(self.clear_requested.emit)
        toolbar.addWidget(self._btn_clear, 0, Qt.AlignVCenter)

        self._btn_save = QtWidgets.QPushButton(tr("save", "Save"))
        self._btn_save.setMaximumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH)
        self._btn_save.setFixedHeight(control_height)
        self._btn_save.setAccessibleName(tr("btn_save_a11y", "Save logs"))
        self._btn_save.setAccessibleDescription(tr("btn_save_desc_a11y", "Click to save log messages to file"))
        self._register_button(self._btn_save, "primary")
        self._btn_save.clicked.connect(self.save_requested.emit)
        toolbar.addWidget(self._btn_save, 0, Qt.AlignVCenter)
        
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
        self._combined_log_widgets['CPU1'] = cpu1_log
        cpu1_layout.addWidget(cpu1_log, 1)
        
        layout.addLayout(cpu1_layout, 1)
        
        # CPU2 column
        cpu2_layout = QtWidgets.QVBoxLayout()
        cpu2_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        
        cpu2_label = QtWidgets.QLabel(tr("send_to_cpu2", "CPU2"))
        cpu2_layout.addWidget(cpu2_label, 0)
        
        cpu2_log = self._create_log_edit()
        self._combined_log_widgets['CPU2'] = cpu2_log
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
        """Create a read-only log text edit widget with drag-and-drop support."""
        edit = DropableTextEdit()
        edit.setReadOnly(True)
        edit.setFont(Fonts.get_monospace_font())
        edit.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        edit.setUndoRedoEnabled(False)
        # Set maximum line count as safety net
        edit.document().setMaximumBlockCount(ConsoleLimits.MAX_DOCUMENT_LINES)
        
        # Enable context menu
        edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        edit.customContextMenuRequested.connect(lambda pos: self._show_context_menu(edit, pos))
        
        return edit
    
    def _show_context_menu(self, text_edit: QtWidgets.QTextEdit, pos: QtCore.QPoint) -> None:
        """Show context menu for the text edit."""
        menu = text_edit.createStandardContextMenu()
        
        # Add custom actions
        menu.addSeparator()
        
        # Copy all visible text
        copy_all_action = QtWidgets.QAction(tr("copy_all", "Copy All"), menu)
        copy_all_action.triggered.connect(lambda: self._copy_all_text(text_edit))
        menu.addAction(copy_all_action)
        
        # Filter by selection
        cursor = text_edit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            filter_action = QtWidgets.QAction(f"{tr('filter', 'Filter')}: {selected_text[:20]}...", menu)
            filter_action.triggered.connect(lambda: self._filter_by_text(selected_text))
            menu.addAction(filter_action)
        
        menu.exec(text_edit.mapToGlobal(pos))
    
    def _copy_all_text(self, text_edit: QtWidgets.QTextEdit) -> None:
        """Copy all text from the text edit to clipboard."""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text_edit.toPlainText())
    
    def _filter_by_text(self, text: str) -> None:
        """Filter logs by the given text."""
        self.search_changed.emit(text)
    
    def _create_tab_header(self, port_label: str) -> QtWidgets.QLabel:
        """Create header label for a log tab."""
        label = QtWidgets.QLabel(port_label)
        return label
    
    def _truncate_html(self, html_content: str) -> str:
        """
        Truncate HTML content to prevent performance issues with very long lines.
        
        Args:
            html_content: HTML formatted content
            
        Returns:
            Truncated HTML content with ellipsis indicator
        """
        if len(html_content) <= ConsoleLimits.MAX_HTML_LENGTH:
            return html_content
        
        # Truncate and add indicator
        truncated = html_content[:ConsoleLimits.MAX_HTML_LENGTH]
        # Close any unclosed tags at the end
        truncated += "...<span style='color:gray'> [truncated]</span>"
        return truncated
    
    def _init_update_timer(self) -> None:
        """Initialize the throttled update timer."""
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._flush_pending_updates)
        
        # Initialize search debounce timer
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
    
    def _perform_search(self) -> None:
        """Execute the actual search operation."""
        self.search_changed.emit(self._search_text)
    
    def _flush_pending_updates(self) -> None:
        """Flush all pending log updates to UI."""
        for port_label, updates in self._pending_updates.items():
            if port_label in self._log_widgets:
                widget = self._log_widgets[port_label]
                if widget.text_edit:
                    # Batch all updates for this port
                    combined_html = "".join([u[0] for u in updates])
                    truncated_html = self._truncate_html(combined_html)
                    widget.text_edit.append(truncated_html)
                    # Trim old content to prevent memory exhaustion
                    self._trim_document_if_needed(widget.text_edit)
                    self._append_to_combined(port_label, truncated_html)
        self._pending_updates.clear()

    def _append_to_combined(self, port_label: str, html_chunk: str) -> None:
        """Mirror CPU1/CPU2 updates inside the combined tab."""
        if port_label not in self._combined_log_widgets:
            return
        text_edit = self._combined_log_widgets[port_label]
        text_edit.append(html_chunk)
        self._trim_document_if_needed(text_edit)
    
    def _trim_document_if_needed(self, text_edit: QtWidgets.QTextEdit) -> None:
        """
        Trim document content if it exceeds MAX_DOCUMENT_LINES.
        Uses block-based removal for better performance.
        """
        doc = text_edit.document()
        max_lines = ConsoleLimits.MAX_DOCUMENT_LINES
        
        # Use blockCount for faster line counting
        if doc.blockCount() > max_lines:
            cursor = QtWidgets.QTextCursor(doc)
            cursor.movePosition(QtGui.QTextCursor.Start)
            
            # Calculate how many lines to remove
            lines_to_remove = doc.blockCount() - max_lines + ConsoleLimits.TRIM_CHUNK_SIZE
            
            # Move down and select, then delete using deleteChar()
            for _ in range(lines_to_remove):
                cursor.movePosition(QtGui.QTextCursor.Down, QtGui.QTextCursor.KeepAnchor)
            cursor.deleteChar()
    
    def append_log(self, port_label: str, html_content: str, plain_text: str) -> None:
        """
        Append log content to a specific port's log.
        Uses throttled updates for better performance.
        
        Args:
            port_label: Port identifier (CPU1, CPU2, TLM)
            html_content: HTML formatted content
            plain_text: Plain text version
        """
        # Add to cache immediately (deque with maxlen handles size limit automatically)
        if port_label not in self._log_cache:
            # Use deque with maxlen for O(1) automatic size limiting
            self._log_cache[port_label] = deque(maxlen=self._max_lines)
        
        self._log_cache[port_label].append((html_content, plain_text))
        
        # Queue UI update for throttling
        if port_label not in self._pending_updates:
            self._pending_updates[port_label] = []
        self._pending_updates[port_label].append((html_content, plain_text))
        
        # Trigger timer if not already running
        if self._update_timer and not self._update_timer.isActive():
            self._update_timer.start(self._update_interval_ms)
    
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
        
        # Remove trailing line endings and убрать пустые строки
        text = text.rstrip('\r\n')
        lines = [line for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        
        header_parts = []
        colors = self._colors
        timestamp = QtCore.QDateTime.currentDateTime().toString('hh:mm:ss')
        if self._show_time:
            header_parts.append(f"<span style='color:{colors.timestamp}'>[{timestamp}]</span>")
        if self._show_source:
            label_color = {
                "RX": colors.rx_label,
                "TX": colors.tx_label,
                "SYS": colors.sys_label,
            }.get(msg_type, colors.sys_label)
            header_parts.append(f"<b style='color:{label_color}'>{msg_type}({port_label}):</b>")
        header = " ".join(header_parts).strip()

        body_color = {
            "RX": colors.rx_text,
            "TX": colors.tx_text,
            "SYS": colors.sys_text,
        }.get(msg_type, colors.sys_text)

        header_html = f"{header} " if header else ""

        return (
            "<div style='white-space:pre-wrap; margin:0 0 0.25em 0'>"
            f"{header_html}<span style='color:{body_color}'>{html.escape(text)}</span>"
            "</div>"
        )

    def _current_theme(self) -> str:
        return "light" if theme_manager.is_light_theme() else "dark"

    def _on_theme_changed(self, theme: str) -> None:
        self._colors = config_loader.get_colors(theme)
        self._apply_theme_to_buttons()
        
        # Применяем тему к контейнеру toolbar и всем его дочерним виджетам
        if hasattr(self, '_toolbar_container'):
            # Обновляем themeClass на контейнере
            theme_class = "light" if theme_manager.is_light_theme() else "dark"
            self._toolbar_container.setProperty("themeClass", theme_class)
            
            # Применяем тему ко всем дочерним виджетам в toolbar для согласованности
            toolbar_widgets = self._toolbar_container.findChildren(QtWidgets.QWidget)
            for widget in toolbar_widgets:
                widget.setProperty("themeClass", theme_class)
            
            # Используем polish для плавного обновления стилей без полной перерисовки
            self._toolbar_container.style().unpolish(self._toolbar_container)
            self._toolbar_container.style().polish(self._toolbar_container)
            self._toolbar_container.update()
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search text change with debouncing."""
        self._search_text = text
        # Restart the debounce timer (300ms delay)
        self._search_timer.start(300)
    
    def _on_display_option_changed(self) -> None:
        """Handle display option change."""
        self._show_time = self._chk_time.isChecked()
        self._show_source = self._chk_source.isChecked()
    
    def clear_all(self) -> None:
        """Clear all logs."""
        for port_label, widget in self._log_widgets.items():
            if widget.text_edit:
                widget.text_edit.clear()
        for text_edit in self._combined_log_widgets.values():
            text_edit.clear()
        
        self._log_cache.clear()
    
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
        button.update()
