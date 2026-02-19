"""
ConsolePanelView: UI component for displaying serial console logs.
Reusable widget for showing RX/TX data from multiple ports.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Signal, Qt, QTimer
from collections import deque
import html
import re

from src.utils.translator import tr, translator
from src.styles.constants import Fonts, Sizes, ConsoleLimits
from src.utils.config_loader import config_loader
from src.utils.theme_manager import theme_manager
from src.utils.icon_cache import get_icon, IconCache


class LogWidget:
    """Container for log widget and its label."""
    __slots__ = ('label', 'text_edit')
    
    def __init__(self):
        self.label: QtWidgets.QLabel | None = None
        self.text_edit: QtWidgets.QTextEdit | None = None


class DropableTextEdit(QtWidgets.QTextEdit):
    """QTextEdit with drag-and-drop support for text files."""
    
    SUPPORTED_EXTENSIONS = ('.txt', '.log', '.hex', '.bin', '.csv')
    file_dropped = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def _is_valid_file(self, path: str) -> bool:
        """Check if file has supported extension."""
        return path.endswith(self.SUPPORTED_EXTENSIONS)
    
    def _has_valid_url(self, mime) -> bool:
        """Check if any URL in mime data is a valid local file."""
        return any(
            url.isLocalFile() and self._is_valid_file(url.toLocalFile())
            for url in mime.urls()
        )
    
    def _get_first_valid_url(self, mime) -> str | None:
        """Get first valid file URL from mime data."""
        for url in mime.urls():
            if url.isLocalFile() and (path := url.toLocalFile()):
                if self._is_valid_file(path):
                    return path
        return None
    
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Handle drag enter event."""
        mime = event.mimeData()
        if mime.hasUrls() and self._has_valid_url(mime):
            event.acceptProposedAction()
        elif mime.hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Handle drag move event."""
        event.acceptProposedAction()
    
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handle drop event - emit file path or text."""
        mime = event.mimeData()
        if mime.hasUrls():
            if path := self._get_first_valid_url(mime):
                self.file_dropped.emit(path)
                event.acceptProposedAction()
        elif mime.hasText():
            self.file_dropped.emit(mime.text())
            event.acceptProposedAction()
    
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle keyboard shortcuts."""
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_F:
            self.toggle_search_bar()
            event.accept()
            return
        super().keyPressEvent(event)


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
        parent: QtWidgets.QWidget | None = None,
        config: dict | None = None
    ):
        """
        Initialize ConsolePanelView.
        
        Args:
            parent: Parent widget
            config: Optional configuration dictionary
        """
        super().__init__(parent)
        
        # Enable keyboard focus for Ctrl+F shortcut
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        self._config = config or {}
        self._port_labels: list[str] = ['CPU1', 'CPU2', 'TLM']
        self._log_widgets: dict[str, LogWidget] = {}
        self._combined_log_widgets: dict[str, QtWidgets.QTextEdit] = {}
        # Use deque with maxlen for O(1) cache operations
        self._log_cache: dict[str, deque] = {}
        # Maximum number of lines in cache for one port
        from src.styles.constants import ConsoleLimits as _ConsoleLimits  # local import to avoid cycles
        self._max_lines: int = int(self._config.get('max_lines', _ConsoleLimits.MAX_CACHE_LINES))
        
        # Display options
        self._show_time: bool = True
        self._show_source: bool = True
        
        # Search filter
        self._search_text: str = ""
        
        # Throttled update state
        self._pending_updates: dict[str, list[tuple]] = {}
        self._update_timer: QTimer | None = None
        self._update_interval_ms: int = 50  # Batch updates every 50ms
        
        # Search debounce timer (300ms)
        self._search_timer: QTimer | None = None
        self._search_debounce_ms: int = 300
        
        # Search highlighting state
        self._search_results: list[tuple] = []  # (port_label, line_idx, block_pos, match_offset, match_length, matched_text)
        self._current_result_index: int = -1
        self._current_highlight_color: str = ""  # Track current theme for highlight updates
        
        self._themed_buttons: list[QtWidgets.QPushButton] = []
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
        
        # Toolbar in separate container for styling
        self._toolbar_container = QtWidgets.QWidget()
        self._toolbar_container.setObjectName("console_toolbar_container")
        self._toolbar_container.setMinimumHeight(50)  # Minimum height for correct centering
        self._toolbar_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        
        # Set themeClass based on effective theme for consistent style application
        effective_theme = theme_manager._get_effective_theme()
        theme_class = "light" if effective_theme == "light" else "dark"
        self._toolbar_container.setProperty("themeClass", theme_class)
        
        toolbar_layout = QtWidgets.QVBoxLayout(self._toolbar_container)
        toolbar_layout.setContentsMargins(10, 0, 10, 8)
        toolbar_layout.setSpacing(8)

        search_row, controls_row = self._create_toolbar()
        toolbar_layout.addLayout(search_row)
        toolbar_layout.addLayout(controls_row)

        layout.addWidget(self._toolbar_container)
        
        # Tab widget for different log views
        self._tab_widget = QtWidgets.QTabWidget()
        self._tab_widget.setObjectName("console_tabs")
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(False)
        # Prevent text truncation in tabs
        self._tab_widget.setElideMode(QtCore.Qt.ElideNone)
        
        # Create tabs for each port
        self._create_log_tabs()
        
        layout.addWidget(self._tab_widget, 1)
        
        self.setLayout(layout)

    def _create_toolbar(self) -> tuple[QtWidgets.QHBoxLayout, QtWidgets.QHBoxLayout]:
        """Create vertical toolbar with search (row 1) and controls (row 2)."""
        control_height = Sizes.INPUT_MIN_HEIGHT

        # --- Row 1: Search ---
        search_row = QtWidgets.QHBoxLayout()
        search_row.setSpacing(Sizes.TOOLBAR_SPACING)
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setAlignment(Qt.AlignVCenter)

        self._search_label = QtWidgets.QLabel(tr("search", "Search:"))
        self._search_label.setAlignment(Qt.AlignVCenter)
        self._search_label.setFixedHeight(control_height)
        self._search_label.setVisible(False)
        search_row.addWidget(self._search_label, 0, Qt.AlignVCenter)

        self._search_edit = QtWidgets.QLineEdit()
        self._search_edit.setPlaceholderText(tr("search_logs", "Search logs..."))
        self._search_edit.setFixedHeight(control_height)
        self._search_edit.setAccessibleName(tr("search_a11y", "Search logs"))
        self._search_edit.setAccessibleDescription(tr("search_desc_a11y", "Enter text to filter log messages"))
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._search_edit.setVisible(False)
        search_row.addWidget(self._search_edit, 1, Qt.AlignVCenter)
        
        # Regex checkbox
        self._chk_regex = QtWidgets.QCheckBox(tr("regex", "Regex"))
        self._chk_regex.setFixedHeight(control_height)
        self._chk_regex.setAccessibleName(tr("regex_a11y", "Enable regular expression search"))
        self._chk_regex.setAccessibleDescription(tr("regex_desc_a11y", "Toggle to use regular expression in search"))
        self._chk_regex.stateChanged.connect(self._on_search_changed)
        self._chk_regex.setVisible(False)
        search_row.addWidget(self._chk_regex, 0, Qt.AlignVCenter)

        search_meta = QtWidgets.QWidget()
        search_meta_layout = QtWidgets.QHBoxLayout(search_meta)
        search_meta_layout.setContentsMargins(0, 0, 0, 0)
        search_meta_layout.setSpacing(4)

        self._search_results_label = QtWidgets.QLabel()
        self._search_results_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self._search_results_label.setFixedHeight(control_height)
        self._search_results_label.setMinimumWidth(80)
        self._search_results_label.setVisible(False)
        self._search_results_label.setObjectName("console_search_results")
        search_meta_layout.addWidget(self._search_results_label)

        self._btn_prev_result = QtWidgets.QToolButton()
        self._btn_prev_result.setArrowType(Qt.LeftArrow)
        self._btn_prev_result.setObjectName("console_prev_match")
        self._btn_prev_result.setFixedSize(control_height, control_height)
        self._btn_prev_result.setAccessibleName(tr("prev_match", "Previous match"))
        self._btn_prev_result.setToolTip(tr("prev_match", "Previous match"))
        self._btn_prev_result.setVisible(False)
        self._btn_prev_result.clicked.connect(self._jump_to_previous_result)
        search_meta_layout.addWidget(self._btn_prev_result)

        self._btn_next_result = QtWidgets.QToolButton()
        self._btn_next_result.setArrowType(Qt.RightArrow)
        self._btn_next_result.setObjectName("console_next_match")
        self._btn_next_result.setFixedSize(control_height, control_height)
        self._btn_next_result.setAccessibleName(tr("next_match", "Next match"))
        self._btn_next_result.setToolTip(tr("next_match", "Next match"))
        self._btn_next_result.setVisible(False)
        self._btn_next_result.clicked.connect(self._jump_to_next_result)
        search_meta_layout.addWidget(self._btn_next_result)

        search_row.addWidget(search_meta, 0, Qt.AlignRight)

        # --- Row 2: Display options + action buttons ---
        controls_row = QtWidgets.QHBoxLayout()
        controls_row.setSpacing(Sizes.TOOLBAR_SPACING)
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setAlignment(Qt.AlignVCenter)

        self._show_label = QtWidgets.QLabel(tr("show", "Show:"))
        self._show_label.setAlignment(Qt.AlignVCenter)
        self._show_label.setFixedHeight(control_height)
        controls_row.addWidget(self._show_label, 0, Qt.AlignVCenter)

        self._chk_time = QtWidgets.QCheckBox(tr("time", "Time"))
        self._chk_time.setChecked(True)
        self._chk_time.setFixedHeight(control_height)
        self._chk_time.setAccessibleName(tr("chk_time_a11y", "Show timestamp"))
        self._chk_time.setAccessibleDescription(tr("chk_time_desc_a11y", "Toggle display of timestamp in log messages"))
        self._chk_time.stateChanged.connect(self._on_display_option_changed)
        controls_row.addWidget(self._chk_time, 0, Qt.AlignVCenter)

        self._chk_source = QtWidgets.QCheckBox(tr("source", "Source"))
        self._chk_source.setChecked(False)
        self._chk_source.setFixedHeight(control_height)
        self._chk_source.setAccessibleName(tr("chk_source_a11y", "Show source"))
        self._chk_source.setAccessibleDescription(tr("chk_source_desc_a11y", "Toggle display of message source in log messages"))
        self._chk_source.stateChanged.connect(self._on_display_option_changed)
        controls_row.addWidget(self._chk_source, 0, Qt.AlignVCenter)

        controls_row.addStretch()

        self._btn_clear = QtWidgets.QPushButton(" " + tr("clear", "Clear"))
        self._btn_clear.setIcon(get_icon("trash"))
        self._btn_clear.setMaximumWidth(Sizes.BUTTON_CLEAR_MAX_WIDTH)
        self._btn_clear.setFixedHeight(control_height)
        self._btn_clear.setAccessibleName(tr("btn_clear_a11y", "Clear logs"))
        self._btn_clear.setAccessibleDescription(tr("btn_clear_desc_a11y", "Click to clear all log messages"))
        self._register_button(self._btn_clear, "danger")
        self._btn_clear.clicked.connect(self.clear_requested.emit)
        controls_row.addWidget(self._btn_clear, 0, Qt.AlignVCenter)

        self._btn_save = QtWidgets.QPushButton(" " + tr("save", "Save"))
        self._btn_save.setIcon(get_icon("floppy-disk"))
        self._btn_save.setMaximumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH)
        self._btn_save.setFixedHeight(control_height)
        self._btn_save.setAccessibleName(tr("btn_save_a11y", "Save logs"))
        self._btn_save.setAccessibleDescription(tr("btn_save_desc_a11y", "Click to save log messages to file"))
        self._register_button(self._btn_save, "primary")
        self._btn_save.clicked.connect(self.save_requested.emit)
        controls_row.addWidget(self._btn_save, 0, Qt.AlignVCenter)

        return search_row, controls_row
    
    def _create_log_tabs(self) -> None:
        """Create log tabs for each port and combined view."""
        
        # Icon mapping for ports
        PORT_ICONS = {
            "CPU1": "paper-plane",
            "CPU2": "paper-plane",
            "TLM": "magnifying-glass",
        }
        
        # Combined tab (CPU1 + CPU2)
        combined_widget = self._create_combined_widget()
        self._tab_widget.addTab(combined_widget, tr("combined", "1+2"))
        self._tab_widget.setTabIcon(0, get_icon("paper-plane"))
        
        # Individual tabs
        for i, port_label in enumerate(self._port_labels):
            tab_widget = self._create_single_log_widget(port_label)
            self._tab_widget.addTab(tab_widget, tr(port_label.lower(), port_label))
            # Set icon for each tab based on port
            tab_index = i + 1  # +1 because combined is index 0
            self._tab_widget.setTabIcon(tab_index, get_icon(PORT_ICONS.get(port_label, "paper-plane")))
    
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
        """Execute the actual search operation with highlighting."""
        
        # First, flush any pending updates to ensure data is synced
        self._flush_pending_updates()
        
        search_text = self._search_text.strip()
        
        # Clear highlights if search is empty
        if not search_text:
            self._clear_all_highlights()
            self._search_results = []
            self._current_result_index = -1
            self._update_search_controls(0)
            return
        
        # Search through all logs - search directly in QTextEdit documents
        self._search_results = []
        self._current_result_index = -1
        
        # Check if regex mode is enabled
        use_regex = getattr(self, '_chk_regex', None) and self._chk_regex.isChecked()
        
        try:
            if use_regex:
                # Use the search text as-is for regex
                pattern = re.compile(search_text, re.IGNORECASE)
            else:
                # Escape special characters for literal search
                pattern = re.compile(re.escape(search_text), re.IGNORECASE)
        except re.error:
            pattern = None
        
        # Define search order: Combined (1+2), CPU1, CPU2, TLM
        search_order = []
        
        # First: Combined tab (CPU1+CPU2 together)
        if 'CPU1' in self._combined_log_widgets and 'CPU2' in self._combined_log_widgets:
            # Combined widgets are Direct QTextEdit, not LogWidget
            combined_widgets = {}
            for k, v in self._combined_log_widgets.items():
                # Create wrapper with text_edit attribute
                wrapper = type('LogWidget', (), {'text_edit': v})()
                combined_widgets[k] = wrapper
            search_order.append(('COMBINED', combined_widgets, 'COMBINED'))
        
        # Then individual ports in order: CPU1, CPU2, TLM
        for port_label in ['CPU1', 'CPU2', 'TLM']:
            if port_label in self._log_widgets:
                search_order.append((port_label, {port_label: self._log_widgets[port_label]}, port_label))
        
        # Search in defined order
        for port_group_label, widgets, tab_name in search_order:
            for port_label, widget in widgets.items():
                # Handle both LogWidget (with .text_edit) and direct QTextEdit
                text_edit = getattr(widget, 'text_edit', widget)
                if not text_edit:
                    continue
                
                document = text_edit.document()
                block_count = document.blockCount()
                
                # Iterate through all blocks in the document
                block = document.begin()
                while block.isValid():
                    plain_text = block.text()
                    
                    if pattern:
                        matches = list(pattern.finditer(plain_text))
                    else:
                        # Simple case-insensitive search
                        matches = []
                        search_lower = search_text.lower()
                        text_lower = plain_text.lower()
                        start = 0
                        while True:
                            pos = text_lower.find(search_lower, start)
                            if pos == -1:
                                break
                            # Create a simple match object
                            class SimpleMatch:
                                __slots__ = ('_start', '_end')
                                
                                def __init__(self, start_pos, end_pos):
                                    self._start = start_pos
                                    self._end = end_pos
                                def start(self):
                                    return self._start
                                def end(self):
                                    return self._end
                                def group(self):
                                    return plain_text[self._start:self._end]
                            
                            matches.append(SimpleMatch(pos, pos + len(search_text)))
                            start = pos + 1
                    
                    for match in matches:
                        match_start = match.start()
                        match_end = match.end()
                        matched_text = match.group()
                        
                        # Store: (port_label, block_position, match_offset, match_length, matched_text, tab_name)
                        # tab_name is 'COMBINED' for combined tab, or port_label for individual tabs
                        self._search_results.append((
                            port_label,
                            block.position(),  # block position in document
                            match_start,
                            match_end - match_start,
                            matched_text,
                            'COMBINED' if port_group_label == 'COMBINED' else port_label  # tab name
                        ))
                    
                    block = block.next()
        
        
        match_count = len(self._search_results)
        self._current_result_index = 0 if match_count else -1
        self._update_search_controls(match_count)

        self._highlight_all_matches()

        if match_count:
            self._scroll_to_current_result()
    
    def _update_search_controls(self, match_count: int) -> None:
        """Update visibility of search navigation controls based on match count."""
        has_results = match_count > 0
        self._btn_prev_result.setVisible(has_results)
        self._btn_next_result.setVisible(has_results)
        
        # Update result count label if it exists
        if hasattr(self, '_lbl_result_count'):
            if has_results:
                self._lbl_result_count.setText(f"{self._current_result_index + 1}/{match_count}")
                self._lbl_result_count.setVisible(True)
            else:
                self._lbl_result_count.setVisible(False)
    
    def _clear_all_highlights(self) -> None:
        """Clear all search highlights from all log widgets."""
        for widget in self._log_widgets.values():
            if widget.text_edit:
                widget.text_edit.setExtraSelections([])
        for text_edit in self._combined_log_widgets.values():
            text_edit.setExtraSelections([])
    
    def _highlight_all_matches(self) -> None:
        """Highlight all search matches in all log widgets."""
        from src.styles.constants import Colors
        

        # Use search colors from constants
        match_color = Colors.SEARCH_MATCH_COLOR
        current_color = Colors.SEARCH_CURRENT_COLOR
        
        # Clear all highlights first
        self._clear_all_highlights()
        
        # Apply highlights to individual port widgets (CPU1, CPU2, TLM)
        for port_label, widget in self._log_widgets.items():
            if not widget.text_edit:
                continue
            
            text_edit = widget.text_edit
            document = text_edit.document()
            
            
            selections = []
            
            # Find all results for this port - use block position directly
            for idx, result in enumerate(self._search_results):
                result_port = result[0]
                if result_port != port_label:
                    continue
                
                block_position = result[1]  # Block position in document
                match_offset = result[2]
                match_length = result[3]
                
                
                # Find the block by position
                block = document.findBlock(block_position)
                if not block.isValid():
                    continue
                
                # Create selection
                cursor = QtGui.QTextCursor(block)
                cursor.setPosition(block.position() + match_offset)
                cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, match_length)
                
                # Use orange for current, gray for others
                if idx == self._current_result_index:
                    # Current selection - orange
                    color = QtGui.QColor(*current_color)
                else:
                    # All matches - gray
                    color = QtGui.QColor(*match_color)
                
                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(color)
                selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, False)
                selections.append(selection)
            
            text_edit.setExtraSelections(selections)
        
        # Apply highlights to Combined tab widgets (CPU1 and CPU2 in combined view)
        for combined_key, text_edit in self._combined_log_widgets.items():
            if not text_edit:
                continue
            
            document = text_edit.document()
            
            
            selections = []
            
            # Find all results for this combined port
            for idx, result in enumerate(self._search_results):
                result_port = result[0]
                result_tab = result[4] if len(result) > 4 else 'individual'  # Check which tab this result is for
                
                # Match if port matches AND tab is 'combined' or port name matches
                if result_port != combined_key and result_tab != 'combined':
                    continue
                
                block_position = result[1]
                match_offset = result[2]
                match_length = result[3]
                
                
                # Find the block by position
                block = document.findBlock(block_position)
                if not block.isValid():
                    continue
                
                # Create selection
                cursor = QtGui.QTextCursor(block)
                cursor.setPosition(block.position() + match_offset)
                cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, match_length)
                
                # Use orange for current, gray for others
                if idx == self._current_result_index:
                    color = QtGui.QColor(*current_color)
                else:
                    color = QtGui.QColor(*match_color)
                
                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(color)
                selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, False)
                selections.append(selection)
            
            text_edit.setExtraSelections(selections)
    
    def _scroll_to_current_result(self) -> None:
        """Scroll to and highlight the current search result."""
        
        if not self._search_results or self._current_result_index < 0:
            return
        
        result = self._search_results[self._current_result_index]
        port_label = result[0]
        block_position = result[1]
        match_offset = result[2]
        match_length = result[3]
        tab_name = result[5] if len(result) > 5 else port_label  # Get tab name
        
        
        # Switch to the tab with this port
        self._switch_to_tab_with_port(port_label, tab_name)
        
        # Scroll to the line after tab switch - pass port_label and tab_name for correct widget selection
        QTimer.singleShot(50, lambda: self._scroll_to_line(block_position, match_offset, match_length, port_label, tab_name))
    
    def _switch_to_tab_with_port(self, port_label: str, tab_name: str = None) -> None:
        """Switch to the tab containing the specified port."""
        
        # If tab_name is COMBINED, switch to the first tab (Combined view)
        if tab_name == 'COMBINED':
            self._tab_widget.setCurrentIndex(0)
            return
        
        # Find the tab index for this port
        for i in range(self._tab_widget.count()):
            tab_text = self._tab_widget.tabText(i)
            if port_label in tab_text:
                self._tab_widget.setCurrentIndex(i)
                return
    
    def _scroll_to_line(self, block_position: int, match_offset: int, match_length: int, port_label: str = None, tab_name: str = None) -> None:
        """Scroll to a specific block and highlight the match."""
       
        text_edit = None
        
        # For Combined tab, use the specific widget (CPU1 or CPU2)
        if tab_name == 'COMBINED' and port_label in self._combined_log_widgets:
            text_edit = self._combined_log_widgets[port_label]
        else:
            # Get current tab's text edit
            current_index = self._tab_widget.currentIndex()

            
            current_tab = self._tab_widget.widget(current_index)
            
            # Find text edit in tab
            text_edits = current_tab.findChildren(QtWidgets.QTextEdit)

            
            text_edit = text_edits[0]
        
            
        document = text_edit.document()
        
        
        # Find the block by position
        block = document.findBlock(block_position)
        
        
        # Move cursor to position (without selecting) for scrolling
        cursor = QtGui.QTextCursor(block)
        cursor.setPosition(block.position() + match_offset)
        
        # Set cursor position for scrolling (no native selection)
        text_edit.setTextCursor(cursor)
        
        # Ensure the cursor is visible by scrolling
        text_edit.ensureCursorVisible()
    
    def _jump_to_next_result(self) -> None:
        """Jump to the next search result."""
        if not self._search_results:
            return
        
        self._current_result_index = (self._current_result_index + 1) % len(self._search_results)
        
        # Update highlights
        self._highlight_all_matches()
        
        # Scroll to the new result
        self._scroll_to_current_result()
    
    def _jump_to_previous_result(self) -> None:
        """Jump to the previous search result."""
        if not self._search_results:
            return
        
        self._current_result_index = (self._current_result_index - 1) % len(self._search_results)
        
        # Update highlights
        self._highlight_all_matches()
        
        # Scroll to the new result
        self._scroll_to_current_result()
    
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
        
        # Remove trailing line endings and remove empty lines
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
        self._update_icons_on_theme_change()
        # Process events to ensure icons are updated
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Apply theme to toolbar container and all its child widgets
        if hasattr(self, '_toolbar_container'):
            # Update themeClass on container
            theme_class = "light" if theme_manager.is_light_theme() else "dark"
            self._toolbar_container.setProperty("themeClass", theme_class)
            
            # Apply theme to all child widgets in toolbar for consistency
            toolbar_widgets = self._toolbar_container.findChildren(QtWidgets.QWidget)
            for widget in toolbar_widgets:
                widget.setProperty("themeClass", theme_class)
            
            # Use polish for smooth style update without full redraw
            self._toolbar_container.style().unpolish(self._toolbar_container)
            self._toolbar_container.style().polish(self._toolbar_container)
            self._toolbar_container.update()

    def _apply_theme_to_button(self, button: QtWidgets.QPushButton) -> None:
        """Apply theme class to a single button for consistent styling."""
        is_light = theme_manager.is_light_theme()
        class_name = "light" if is_light else "dark"
        button.setProperty("class", class_name)

    def _update_icons_on_theme_change(self) -> None:
        """Update all button icons when theme changes."""
        # Update clear button icon
        if hasattr(self, '_btn_clear'):
            self._btn_clear.setIcon(get_icon("trash"))
            self._btn_clear.update()
        
        # Update save button icon
        if hasattr(self, '_btn_save'):
            self._btn_save.setIcon(get_icon("floppy-disk"))
            self._btn_save.update()
        
        # Update tab icons
        self._update_tab_icons()
    
    def _update_tab_icons(self) -> None:
        """Update tab icons for all port tabs."""
        if not hasattr(self, '_tab_widget') or not hasattr(self, '_log_widgets'):
            return
        
        # Icon mapping for ports
        PORT_ICONS = {
            "CPU1": "paper-plane",
            "CPU2": "paper-plane",
            "TLM": "magnifying-glass",
        }
        
        # Update combined tab icon
        self._tab_widget.setTabIcon(0, get_icon("paper-plane"))
        
        # Update port-specific tab icons
        tab_index = 1  # Start after combined tab
        for port_label in self._log_widgets.keys():
            self._tab_widget.setTabIcon(tab_index, get_icon(PORT_ICONS.get(port_label, "paper-plane")))
            tab_index += 1
        
        # Force repaint of tab bar
        self._tab_widget.tabBar().update()
    
    def _apply_theme_to_buttons(self) -> None:
        """Update all registered buttons with the active theme class."""
        for button in self._themed_buttons:
            self._apply_theme_to_button(button)

    def _on_search_changed(self, text_or_state) -> None:
        """Handle search text change or regex checkbox change with debouncing."""
        # Check if called from checkbox (int) or text field (str)
        if isinstance(text_or_state, int):
            # Checkbox state changed - restart timer to re-search with new mode
            self._search_timer.start(300)
        else:
            self._search_text = text_or_state
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
    
    def toggle_search_bar(self) -> None:
        """Toggle visibility of the search bar."""
        # Toggle visibility of search-related widgets
        widgets_to_toggle = [
            self._search_label,
            self._search_edit,
            self._chk_regex,
            self._btn_prev_result,
            self._btn_next_result,
            self._search_results_label,
        ]
        
        # Check current visibility state
        currently_visible = self._search_edit.isVisible()
        new_visibility = not currently_visible
        
        for widget in widgets_to_toggle:
            if widget:
                widget.setVisible(new_visibility)
        
        # Focus the search edit when showing
        if new_visibility:
            self._search_edit.setFocus()
    
    def save_logs(self) -> None:
        """Request to save logs."""
        self.save_requested.emit()
    
    def get_logs_text(self, port_label: str | None = None) -> str:
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
    
    def get_log_count(self, port_label: str | None = None) -> int:
        """Get number of log lines."""
        if port_label and port_label in self._log_cache:
            return len(self._log_cache[port_label])
        elif not port_label:
            return sum(len(cache) for cache in self._log_cache.values())
        return 0
    
    def scroll_to_bottom(self, port_label: str | None = None) -> None:
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
        class_name: str | None = None,
    ) -> None:
        if class_name:
            existing = button.property("class")
            if existing:
                classes = set(str(existing).split())
                classes.add(class_name)
                button.setProperty("class", " ".join(sorted(classes)))
            else:
                button.setProperty("class", class_name)
