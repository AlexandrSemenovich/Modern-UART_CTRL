"""Command history dialog with toolbar actions."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6 import QtWidgets, QtCore, QtGui

from src.viewmodels.command_history_viewmodel import (
    CommandHistoryModel,
    CommandHistoryTableModel,
    CommandHistoryEntry,
)
from src.utils.translator import tr, translator
from src.utils.theme_manager import theme_manager
from src.utils.icon_cache import get_icon
from src.styles.constants import Sizes


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
        self._proxy_model.setFilterKeyColumn(-1)
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

        # Use action texts as tooltips in icon-only mode
        for act in (
            self._act_send,
            self._act_edit,
            self._act_delete,
            self._act_clear,
            self._act_export,
        ):
            act.setToolTip(act.text())

        # Search row
        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText(
            tr("history_search_placeholder", "Search...")
        )
        self._search.setMaximumWidth(Sizes.SEARCH_FIELD_MAX_WIDTH)

        search_widget = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(Sizes.LAYOUT_SPACING)
        search_layout.addWidget(self._search)
        layout.addWidget(search_widget)

        # Table
        self._table = QtWidgets.QTableView()
        self._table.setModel(self._proxy_model)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self._table.setAlternatingRowColors(True)
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
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
        bottom_row.addWidget(self._btn_close)

        layout.addLayout(bottom_row)

        self._update_summary()

    def _connect_signals(self) -> None:
        self._search.textChanged.connect(self._proxy_model.setFilterFixedString)
        self._act_send.triggered.connect(self._send_selected)
        self._act_edit.triggered.connect(self._insert_selected)
        self._act_delete.triggered.connect(self._delete_selected)
        self._act_clear.triggered.connect(self._clear_all)
        self._act_export.triggered.connect(self._export_all)
        self._btn_close.clicked.connect(self.close)
        self._table.doubleClicked.connect(self._insert_selected)
        self._model.entries_changed.connect(self._update_summary)
        translator.language_changed.connect(self._on_language_changed)
        theme_manager.theme_changed.connect(self._apply_theme)

    def _selected_entries(self) -> List[CommandHistoryEntry]:
        entries: List[CommandHistoryEntry] = []
        for index in self._table.selectionModel().selectedRows():
            source_index = self._proxy_model.mapToSource(index)
            entry = self._table_model.entry_at(source_index.row())
            if entry:
                entries.append(entry)
        return entries

    def _selected_rows(self) -> List[int]:
        rows: List[int] = []
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

    def _on_language_changed(self, _: str) -> None:
        self.setWindowTitle(tr("command_history", "Command History"))
        self._search.setPlaceholderText(tr("history_search_placeholder", "Search..."))
        self._act_send.setText(tr("history_send", "Send"))
        self._act_edit.setText(tr("history_edit", "Insert"))
        self._act_delete.setText(tr("history_delete", "Delete"))
        self._act_clear.setText(tr("history_clear_all", "Clear All"))
        self._act_export.setText(tr("history_export", "Export"))
        self._btn_close.setText(tr("history_close", "Close"))
        self._update_summary()

    def _apply_theme(self, _: str) -> None:
        theme_class = "light" if theme_manager.is_light_theme() else "dark"
        # Применяем ко всем виджетам и их детям
        widgets = [self, self._toolbar, self._search, self._table, self._lbl_summary, self._btn_close]
        widgets.extend(self.findChildren(QtWidgets.QWidget))
        for widget in widgets:
            widget.setProperty("themeClass", theme_class)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
