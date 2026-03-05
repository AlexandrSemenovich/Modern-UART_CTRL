"""Command history dialog with toolbar actions."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets, QtCore, QtGui

from src.viewmodels.command_history_viewmodel import (
    CommandHistoryModel,
    CommandHistoryTableModel,
    CommandHistoryEntry,
)
from src.utils.translator import tr, translator
from src.utils.theme_manager import theme_manager
from src.utils.icon_cache import get_icon
from src.styles.constants import Sizes, Colors


class CommandHistoryDialog(QtWidgets.QDialog):
    command_selected = QtCore.Signal(str)

    def __init__(self, model: CommandHistoryModel, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(False)
        self.setWindowTitle(tr("command_history", "Command History"))
        self.resize(720, 420)
        self._model = model
        self._table_model = CommandHistoryTableModel(model, self)
        self._proxy_model = QtCore.QSortFilterProxyModel(self)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(0)
        self._proxy_model.setSourceModel(self._table_model)

        self._build_ui()
        self._connect_signals()
        self._apply_theme(theme_manager.get_theme())

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(
            Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN,
            Sizes.LAYOUT_MARGIN,
        )
        layout.setSpacing(Sizes.LAYOUT_SPACING)

        # Compact toolbar with icon-only actions
        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setIconSize(QtCore.QSize(18, 18))
        self._toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        layout.addWidget(self._toolbar)

        self._act_send = self._toolbar.addAction(
            get_icon("paper-plane"),
            tr("history_send", "Send"),
        )
        self._act_edit = self._toolbar.addAction(
            get_icon("floppy-disk"),
            tr("history_edit", "Insert"),
        )
        self._act_delete = self._toolbar.addAction(
            get_icon("trash"),
            tr("history_delete", "Delete"),
        )
        self._toolbar.addSeparator()
        self._act_clear = self._toolbar.addAction(
            get_icon("clock-rotate-left"),
            tr("history_clear_all", "Clear All"),
        )
        self._act_export = self._toolbar.addAction(
            get_icon("floppy-disk"),
            tr("history_export", "Export"),
        )
        self._toolbar_actions = (
            self._act_send,
            self._act_edit,
            self._act_delete,
            self._act_clear,
            self._act_export,
        )
        self._set_toolbar_tooltips()

        # Search row
        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText(
            tr("history_search_placeholder", "Search...")
        )
        self._search.setMaximumWidth(int(Sizes.SEARCH_FIELD_MAX_WIDTH * 6))

        search_widget = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(Sizes.LAYOUT_SPACING)
        search_layout.addWidget(self._search, 1)

        self._search_controls = QtWidgets.QWidget()
        self._search_controls.setObjectName("history_search_controls")
        controls_layout = QtWidgets.QHBoxLayout(self._search_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        control_height = Sizes.INPUT_MIN_HEIGHT

        self._btn_prev_match = QtWidgets.QToolButton()
        self._btn_prev_match.setText(tr("prev_match_symbol", "<"))
        self._btn_prev_match.setObjectName("history_prev_match")
        self._btn_prev_match.setFixedSize(control_height, control_height)
        self._btn_prev_match.setToolTip(tr("prev_match", "Previous match"))
        self._btn_prev_match.setAccessibleName(tr("prev_match", "Previous match"))
        self._btn_prev_match.setVisible(False)
        self._btn_prev_match.clicked.connect(self._jump_to_previous_result)
        controls_layout.addWidget(self._btn_prev_match)

        self._btn_next_match = QtWidgets.QToolButton()
        self._btn_next_match.setText(tr("next_match_symbol", ">"))
        self._btn_next_match.setObjectName("history_next_match")
        self._btn_next_match.setFixedSize(control_height, control_height)
        self._btn_next_match.setToolTip(tr("next_match", "Next match"))
        self._btn_next_match.setAccessibleName(tr("next_match", "Next match"))
        self._btn_next_match.setVisible(False)
        self._btn_next_match.clicked.connect(self._jump_to_next_result)
        controls_layout.addWidget(self._btn_next_match)

        self._lbl_search_results = QtWidgets.QLabel()
        self._lbl_search_results.setObjectName("history_search_results")
        self._lbl_search_results.setMinimumWidth(120)
        self._lbl_search_results.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._lbl_search_results.setAlignment(QtCore.Qt.AlignCenter)
        self._lbl_search_results.setText("\u200b")
        controls_layout.addWidget(self._lbl_search_results)

        self._search_controls.setVisible(False)
        search_layout.addWidget(self._search_controls, 0)
        layout.addWidget(search_widget)

        # Table
        self._table = CommandHistoryTableView(self)
        self._table.setModel(self._proxy_model)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self._table.setAlternatingRowColors(True)
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._set_table_headers()
        self._highlight_delegate = _HistorySearchDelegate(self._table)
        self._table.setItemDelegate(self._highlight_delegate)
        layout.addWidget(self._table)

        # Summary + close aligned to the right
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(Sizes.LAYOUT_SPACING)

        self._lbl_summary = QtWidgets.QLabel()
        bottom_row.addWidget(self._lbl_summary)
        bottom_row.addStretch(1)

        self._btn_close = QtWidgets.QPushButton(tr("history_close", "Close"))
        self._btn_close.setMinimumHeight(Sizes.BUTTON_MIN_HEIGHT)
        self._btn_close.setMaximumWidth(Sizes.BUTTON_MAX_WIDTH)
        self._btn_close.setProperty("class", "btn-secondary")
        self._btn_close.style().unpolish(self._btn_close)
        self._btn_close.style().polish(self._btn_close)
        bottom_row.addWidget(self._btn_close)

        layout.addLayout(bottom_row)

        self._update_summary()

    def _connect_signals(self) -> None:
        self._search.textChanged.connect(self._on_search_text_changed)
        self._act_send.triggered.connect(self._send_selected)
        self._act_edit.triggered.connect(self._insert_selected)
        self._act_delete.triggered.connect(self._delete_selected)
        self._act_clear.triggered.connect(self._clear_all)
        self._act_export.triggered.connect(self._export_all)
        self._btn_close.clicked.connect(self.close)
        self._table.doubleClicked.connect(self._insert_selected)
        self._model.entries_changed.connect(self._on_entries_changed)
        translator.language_changed.connect(self._on_language_changed)
        theme_manager.theme_changed.connect(self._apply_theme)
        self.destroyed.connect(self._disconnect_translator)

    def _disconnect_translator(self) -> None:
        try:
            translator.language_changed.disconnect(self._on_language_changed)
        except (RuntimeError, TypeError):
            pass

    def _selected_entries(self) -> list[CommandHistoryEntry]:
        entries: list[CommandHistoryEntry] = []
        for index in self._table.selectionModel().selectedRows():
            source_index = self._proxy_model.mapToSource(index)
            entry = self._table_model.entry_at(source_index.row())
            if entry:
                entries.append(entry)
        return entries

    def _selected_rows(self) -> list[int]:
        rows: list[int] = []
        for index in self._table.selectionModel().selectedRows():
            rows.append(self._proxy_model.mapToSource(index).row())
        return rows

    def _send_selected(self) -> None:
        entries = self._selected_entries()
        if entries:
            self.command_selected.emit(entries[0].command)

    def _insert_selected(self) -> None:
        entries = self._selected_entries()
        if entries:
            self.command_selected.emit(entries[0].command)
            self.close()

    def _delete_selected(self) -> None:
        rows = self._selected_rows()
        if rows:
            self._model.remove_indices(rows)

    def _clear_all(self) -> None:
        confirm = QtWidgets.QMessageBox.question(
            self,
            tr("history_clear_all", "Clear All"),
            tr("history_confirm_clear", "Clear entire history?"),
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self._model.clear()

    def _export_all(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            tr("history_export", "Export"),
            "command_history.txt",
            tr("text_files_filter", "Text Files (*.txt);;All Files (*)"),
        )
        if path:
            self._model.export_to_file(Path(path))

    def _update_summary(self) -> None:
        count = self._model.entry_count()
        self._lbl_summary.setText(tr("history_total", "{count} entries").format(count=count))

    def _on_entries_changed(self) -> None:
        self._update_summary()
        self._refresh_search_feedback()

    def _on_language_changed(self, _: str) -> None:
        self.setWindowTitle(tr("command_history", "Command History"))
        self._search.setPlaceholderText(tr("history_search_placeholder", "Search..."))
        self._act_send.setText(tr("history_send", "Send"))
        self._act_edit.setText(tr("history_edit", "Insert"))
        self._act_delete.setText(tr("history_delete", "Delete"))
        self._act_clear.setText(tr("history_clear_all", "Clear All"))
        self._act_export.setText(tr("history_export", "Export"))
        self._btn_close.setText(tr("history_close", "Close"))
        self._set_toolbar_tooltips()
        self._set_table_headers()
        self._update_summary()
        self._refresh_search_feedback(retranslate_only=True)
        self._update_navigation_controls()

    def _set_toolbar_tooltips(self) -> None:
        for act in self._toolbar_actions:
            act.setToolTip(act.text())

    def _set_table_headers(self) -> None:
        headers = {
            0: tr("history_column_command", "Command"),
            1: tr("history_column_port", "Port"),
            2: tr("history_column_status", "Status"),
            3: tr("history_column_timestamp", "Timestamp"),
        }
        for column, title in headers.items():
            self._table_model.setHeaderData(column, QtCore.Qt.Horizontal, title)
        if hasattr(self._table_model, "headerDataChanged"):
            self._table_model.headerDataChanged.emit(QtCore.Qt.Horizontal, 0, len(headers) - 1)

    def _apply_theme(self, _: str) -> None:
        theme_class = "light" if theme_manager.is_light_theme() else "dark"
        # Apply to all widgets and their children
        widgets = [self, self._toolbar, self._search, self._table, self._lbl_summary, self._btn_close]
        widgets.extend(self.findChildren(QtWidgets.QWidget))
        for widget in widgets:
            widget.setProperty("themeClass", theme_class)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        
        # Update toolbar action icons for theme
        self._update_toolbar_icons()
        # Process events to ensure icons are updated
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def _update_toolbar_icons(self) -> None:
        """Update toolbar action icons when theme changes."""
        if hasattr(self, '_act_send'):
            self._act_send.setIcon(get_icon("paper-plane"))
        if hasattr(self, '_act_edit'):
            self._act_edit.setIcon(get_icon("floppy-disk"))
        if hasattr(self, '_act_delete'):
            self._act_delete.setIcon(get_icon("trash"))
        if hasattr(self, '_act_clear'):
            self._act_clear.setIcon(get_icon("clock-rotate-left"))
        if hasattr(self, '_act_export'):
            self._act_export.setIcon(get_icon("floppy-disk"))
        
        # Force repaint of toolbar
        if hasattr(self, '_toolbar'):
            self._toolbar.update()

    def _on_search_text_changed(self, text: str) -> None:
        pattern = self._build_search_pattern(text)
        self._apply_search_filter(pattern)
        self._highlight_delegate.set_pattern(pattern)
        self._refresh_search_feedback()

    def _build_search_pattern(self, text: str) -> QtCore.QRegularExpression | None:
        cleaned = text.strip()
        if not cleaned:
            return None
        pattern = QtCore.QRegularExpression(QtCore.QRegularExpression.escape(cleaned))
        pattern.setPatternOptions(QtCore.QRegularExpression.CaseInsensitiveOption)
        return pattern if pattern.isValid() else None

    def _apply_search_filter(self, pattern: QtCore.QRegularExpression | None) -> None:
        if pattern is None:
            self._proxy_model.setFilterRegularExpression(QtCore.QRegularExpression())
            return
        self._proxy_model.setFilterRegularExpression(pattern)

    def _refresh_search_feedback(self, *, retranslate_only: bool = False) -> None:
        pattern = self._highlight_delegate.pattern
        if pattern is None:
            self._lbl_search_results.setText("\u200b")
            self._lbl_search_results.setVisible(False)
            self._search.setProperty("hasMatches", False)
            self._search.style().unpolish(self._search)
            self._search.style().polish(self._search)
            self._search_results = []
            self._current_match_index = -1
            self._highlight_delegate.set_current_match_index(-1)
            self._search_active = False
            self._adjust_search_layout(expanded=True)
            self._update_navigation_controls()
            return

        if retranslate_only:
            count = getattr(self, "_last_match_count", 0)
        else:
            count = self._count_search_matches(pattern)
            self._last_match_count = count

        self._lbl_search_results.setVisible(True)
        self._lbl_search_results.setText(
            tr("history_search_matches", "Matches: {count}").format(count=count)
        )
        has_matches = bool(count)
        self._search.setProperty("hasMatches", has_matches)
        self._search.style().unpolish(self._search)
        self._search.style().polish(self._search)
        self._search_results = self._collect_match_rows(pattern)
        self._current_match_index = 0 if self._search_results else -1
        self._highlight_delegate.set_current_match_index(
            self._search_results[self._current_match_index]
            if self._current_match_index >= 0
            else -1
        )
        self._search_active = True
        self._adjust_search_layout(expanded=not has_matches)
        self._update_navigation_controls()

    def _update_navigation_controls(self) -> None:
        if not getattr(self, "_search_active", False):
            self._lbl_search_results.setText("\u200b")
            self._lbl_search_results.setVisible(False)
            self._btn_prev_match.setVisible(False)
            self._btn_next_match.setVisible(False)
            return

        total_rows = len(getattr(self, "_search_results", []))
        total_matches = getattr(self, "_last_match_count", total_rows)
        has_matches = total_rows > 0
        self._btn_prev_match.setVisible(has_matches)
        self._btn_next_match.setVisible(has_matches)
        self._lbl_search_results.setVisible(True)
        self._search_controls.setVisible(True)
        if not has_matches:
            matches_text = tr("history_search_matches", "Matches: {count}").format(count=total_matches)
            self._lbl_search_results.setText(matches_text)
            return

        matches_text = tr("history_search_matches", "Matches: {count}").format(count=total_matches)
        current_position = self._current_match_index + 1 if self._current_match_index >= 0 else 0
        if current_position and total_rows:
            position_text = tr("position_of", "{current} of {total}").format(
                current=current_position,
                total=total_rows,
            )
            self._lbl_search_results.setText(f"{matches_text} · {position_text}")
        else:
            self._lbl_search_results.setText(matches_text)

    def _adjust_search_layout(self, *, expanded: bool) -> None:
        self._search.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding if expanded else QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed,
        )
        if expanded:
            self._search_controls.hide()
            self._search.setMaximumWidth(int(Sizes.SEARCH_FIELD_MAX_WIDTH * 6))
        else:
            self._search_controls.show()
            self._search.setMaximumWidth(int(Sizes.SEARCH_FIELD_MAX_WIDTH * 2))

    def _collect_match_rows(self, pattern: QtCore.QRegularExpression) -> list[int]:
        rows: list[int] = []
        row_count = self._proxy_model.rowCount()
        for row in range(row_count):
            index = self._proxy_model.index(row, 0)
            value = self._proxy_model.data(index, QtCore.Qt.DisplayRole)
            if not value:
                continue
            if pattern.match(str(value)).hasMatch():
                rows.append(row)
        return rows

    def _jump_to_next_result(self) -> None:
        self._current_match_index = (self._current_match_index + 1) % len(self._search_results)
        self._highlight_delegate.set_current_match_index(self._search_results[self._current_match_index])
        self._scroll_to_current_match()
        self._update_navigation_controls()

    def _jump_to_previous_result(self) -> None:
        self._current_match_index = (self._current_match_index - 1) % len(self._search_results)
        self._highlight_delegate.set_current_match_index(self._search_results[self._current_match_index])
        self._scroll_to_current_match()
        self._update_navigation_controls()

    def _scroll_to_current_match(self) -> None:
        row = self._search_results[self._current_match_index]
        index = self._proxy_model.index(row, 0)
        self._table.selectRow(index.row())
        self._table.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtCenter)

    def _count_search_matches(self, pattern: QtCore.QRegularExpression) -> int:
        if not pattern.isValid():
            return 0
        total = 0
        row_count = self._proxy_model.rowCount()
        for row in range(row_count):
            index = self._proxy_model.index(row, 0)
            value = self._proxy_model.data(index, QtCore.Qt.DisplayRole)
            if not value:
                continue
            iterator = pattern.globalMatch(str(value))
            while iterator.hasNext():
                iterator.next()
                total += 1
        return total


class _HistorySearchDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._pattern: QtCore.QRegularExpression | None = None
        self._match_color = QtGui.QColor(*Colors.SEARCH_MATCH_COLOR)
        self._current_color = QtGui.QColor(*Colors.SEARCH_CURRENT_COLOR)
        self._current_row: int = -1

    def set_current_match_index(self, row: int) -> None:
        self._current_row = row
        parent = self.parent()
        if parent:
            parent.viewport().update()  # type: ignore[call-arg]

    @property
    def pattern(self) -> QtCore.QRegularExpression | None:
        return self._pattern

    def set_pattern(self, pattern: QtCore.QRegularExpression | None) -> None:
        changed = (self._pattern is None) != (pattern is None)
        if self._pattern and pattern:
            changed = self._pattern.pattern() != pattern.pattern()
        self._pattern = pattern
        if changed and self.parent():
            self.parent().viewport().update()  # type: ignore[call-arg]

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        self.initStyleOption(option, index)
        text = option.text or ""
        pattern = self._pattern
        if index.column() != 0 or not text or pattern is None or not pattern.isValid():
            return super().paint(painter, option, index)

        doc = QtGui.QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setPlainText(text)

        iterator = pattern.globalMatch(text)
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(self._match_color)
        while iterator.hasNext():
            match = iterator.next()
            start = match.capturedStart()
            length = match.capturedLength()
            if start < 0 or length <= 0:
                continue
            cursor = QtGui.QTextCursor(doc)
            cursor.setPosition(start)
            cursor.setPosition(start + length, QtGui.QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(fmt)

        option.text = ""
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter)

        painter.save()
        painter.translate(option.rect.topLeft())
        doc.setTextWidth(option.rect.width())
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(QtGui.QPalette.HighlightedText))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()


class CommandHistoryTableView(QtWidgets.QTableView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)

    def startDrag(self, supportedActions: QtCore.Qt.DropActions) -> None:  # type: ignore[override]
        commands = self._collect_selected_commands()
        if not commands:
            return
        text = "\n".join(commands)
        mime = QtCore.QMimeData()
        mime.setText(text)
        mime.setData("application/x-command-history", text.encode("utf-8"))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(self._build_drag_pixmap(text))
        drag.exec(QtCore.Qt.CopyAction)

    def _collect_selected_commands(self) -> list[str]:
        selection = self.selectionModel()
        if not selection:
            return []
        indexes = selection.selectedRows()
        if not indexes:
            return []
        dialog = self.parent()
        source_model = getattr(dialog, "_table_model", None)
        proxy_model = self.model()
        if source_model is None or proxy_model is None:
            return []
        commands: list[str] = []
        for index in indexes:
            source_index = proxy_model.mapToSource(index) if hasattr(proxy_model, "mapToSource") else index
            entry = source_model.entry_at(source_index.row()) if source_model else None
            if entry and entry.command:
                commands.append(entry.command)
        return commands

    def _build_drag_pixmap(self, text: str) -> QtGui.QPixmap:
        truncated = text if len(text) <= 160 else text[:159] + "…"
        lines = truncated.splitlines() or [""]

        font = QtGui.QFont(self.font())
        font.setBold(True)
        metrics = QtGui.QFontMetrics(font)
        line_height = metrics.height()
        padding_x = 24
        padding_y = 16
        content_width = max(metrics.horizontalAdvance(line) for line in lines)
        width = content_width + padding_x
        height = line_height * len(lines) + padding_y

        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        palette = self.palette()
        base_color = palette.color(QtGui.QPalette.Base)
        text_color = palette.color(QtGui.QPalette.Text)
        border_color = palette.color(QtGui.QPalette.Highlight)

        rect = QtCore.QRectF(0.5, 0.5, width - 1, height - 1)
        painter.setPen(QtGui.QPen(border_color, 1))
        painter.setBrush(QtGui.QBrush(base_color))
        painter.drawRoundedRect(rect, 8, 8)

        painter.setFont(font)
        painter.setPen(text_color)
        y = padding_y / 2 + metrics.ascent()
        for line in lines:
            painter.drawText(padding_x / 2, y, line)
            y += line_height

        painter.end()
        return pixmap
