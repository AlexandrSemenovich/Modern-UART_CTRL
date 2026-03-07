"""Widget Host window implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PySide6 import QtCore, QtGui, QtWidgets

from src.styles.constants import Sizes
from src.utils import (
    get_widget_host_viewmodel,
    get_widget_settings_store,
    get_theme_manager,
)
from src.utils.widget_settings_store import WidgetHostState
from src.viewmodels.widget_host_viewmodel import ModuleDockItem, WidgetHostViewModel


@dataclass(slots=True)
class CanvasCell:
    widget: QtWidgets.QWidget


class WidgetCanvas(QtWidgets.QFrame):
    """Grid-like canvas supporting basic drag-and-drop пересортировку."""

    layoutChanged = QtCore.Signal(list)
    dockRemoveRequested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._grid = QtWidgets.QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(Sizes.LAYOUT_SPACING)
        self._grid.setVerticalSpacing(Sizes.LAYOUT_SPACING)
        self._cells: list[CanvasCell] = []

    def attachDock(self, dock: ModuleDockItem) -> None:
        container = DockContainer(dock, self)
        container.removeRequested.connect(self._on_remove_requested)
        container.dragInitiated.connect(self._start_drag)
        self._cells.append(CanvasCell(container))
        self._relayout()

    def removeDock(self, dock_id: str) -> None:
        for idx, cell in enumerate(list(self._cells)):
            if cell.widget.dock_id == dock_id:
                self._clear_cell(idx)
                break
        self._relayout()

    def current_order(self) -> list[str]:
        return [cell.widget.dock_id for cell in self._cells if cell.widget]

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasFormat("application/widget-dock"):
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # type: ignore[override]
        dock_id = event.mimeData().text()
        pos = event.position().toPoint()
        target_index = self._index_from_pos(pos)
        if dock_id and target_index is not None:
            self._move_dock(dock_id, target_index)
            event.acceptProposedAction()

    def _start_drag(self, source: DockContainer) -> None:
        mime = QtCore.QMimeData()
        mime.setData("application/widget-dock", b"1")
        mime.setText(source.dock_id)
        drag = QtGui.QDrag(source)
        drag.setMimeData(mime)
        pixmap = source.grab()
        drag.setPixmap(pixmap)
        drag.exec(QtCore.Qt.MoveAction)

    def _move_dock(self, dock_id: str, target_index: int) -> None:
        for idx, cell in enumerate(self._cells):
            if cell.widget.dock_id == dock_id:
                self._cells.pop(idx)
                self._cells.insert(target_index, cell)
                self._relayout()
                break

    def _relayout(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        columns = max(1, int(max(1, self.width()) / 360))
        for idx, cell in enumerate(self._cells):
            row = idx // columns
            col = idx % columns
            self._grid.addWidget(cell.widget, row, col)
        self.layoutChanged.emit(self.current_order())

    def _index_from_pos(self, pos: QtCore.QPoint) -> int | None:
        for idx, cell in enumerate(self._cells):
            rect = cell.widget.geometry()
            if rect.contains(pos):
                return idx
        return len(self._cells)

    def _on_remove_requested(self, dock_id: str) -> None:
        self.dockRemoveRequested.emit(dock_id)
        self.removeDock(dock_id)

    def _clear_cell(self, index: int) -> None:
        cell = self._cells.pop(index)
        cell.widget.setParent(None)


class DockContainer(QtWidgets.QFrame):
    """Визуальная обёртка вокруг ModuleDockItem.view."""

    removeRequested = QtCore.Signal(str)
    dragInitiated = QtCore.Signal(object)

    def __init__(self, dock: ModuleDockItem, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.dock_id = dock.dock_id
        self._dock = dock
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN)
        layout.setSpacing(Sizes.LAYOUT_SPACING)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(dock.descriptor.title)
        title.setProperty("class", "dock-title")
        header.addWidget(title)
        header.addStretch()

        close_btn = QtWidgets.QToolButton()
        close_btn.setText("×")
        close_btn.clicked.connect(lambda: self.removeRequested.emit(self.dock_id))
        header.addWidget(close_btn)
        layout.addLayout(header)

        dock.view.setParent(self)
        layout.addWidget(dock.view)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == QtCore.Qt.LeftButton:
            self.dragInitiated.emit(self)
        super().mousePressEvent(event)


class WidgetHostWindow(QtWidgets.QWidget):
    """Главное окно для размещения модулей."""

    def __init__(
        self,
        viewmodel: WidgetHostViewModel | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Widget Host")
        self._viewmodel = viewmodel or get_widget_host_viewmodel()
        self._settings = get_widget_settings_store()
        self._theme = get_theme_manager()
        self._canvas = WidgetCanvas(self)
        self._canvas.layoutChanged.connect(self._on_layout_changed)
        self._canvas.dockRemoveRequested.connect(self._remove_module_requested)
        self._viewmodel.modules_changed.connect(self._sync_modules)

        self._build_ui()
        self._apply_saved_geometry()
        self._load_initial_modules()

    # region UI
    def _build_ui(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN, Sizes.LAYOUT_MARGIN)
        main_layout.setSpacing(Sizes.LAYOUT_SPACING)

        toolbar = self._build_toolbar()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self._canvas, 1)

    def _build_toolbar(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Sizes.TOOLBAR_SPACING)

        self._btn_on_top = QtWidgets.QToolButton()
        self._btn_on_top.setText("⬆ Top")
        self._btn_on_top.setCheckable(True)
        self._btn_on_top.clicked.connect(self._toggle_on_top)
        layout.addWidget(self._btn_on_top)

        self._screen_combo = QtWidgets.QComboBox()
        self._screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        layout.addWidget(self._screen_combo)
        self._populate_screens()

        add_button = QtWidgets.QToolButton()
        add_button.setText("+ Module")
        add_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        add_menu = QtWidgets.QMenu(add_button)
        self._module_menu = add_menu
        add_button.setMenu(add_menu)
        layout.addWidget(add_button)
        self._refresh_module_menu()

        layout.addStretch()
        return widget
    # endregion

    # region Handlers
    def showEvent(self, event: QtGui.QShowEvent) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._apply_on_top_state()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        self.save_state()
        event.ignore()
        self.hide()

    def moveEvent(self, event: QtGui.QMoveEvent) -> None:  # type: ignore[override]
        super().moveEvent(event)
        self._schedule_geometry_save()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._schedule_geometry_save()
    # endregion

    # region Actions
    def _toggle_on_top(self) -> None:
        enabled = self._btn_on_top.isChecked()
        self._settings.toggle_on_top(enabled)
        self._apply_on_top_state()

    def _apply_on_top_state(self) -> None:
        state = self._settings.load()
        self._btn_on_top.setChecked(state.always_on_top)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, state.always_on_top)
        self.show()

    def _on_screen_changed(self, index: int) -> None:
        screen = self._screen_combo.itemData(index)
        if isinstance(screen, QtGui.QScreen):
            self._settings.update_screen(screen.name())
            self._move_to_screen(screen)

    def _move_to_screen(self, screen: QtGui.QScreen) -> None:
        geometry = screen.availableGeometry()
        self.move(geometry.center() - self.rect().center())

    def _on_layout_changed(self, order: Iterable[str]) -> None:
        snapshot = {"modules": list(order)}
        self._settings.save_layout_snapshot(snapshot)

    def _sync_modules(self, docks: list[ModuleDockItem]) -> None:
        existing_ids = set(self._canvas.current_order())
        for dock in docks:
            if dock.dock_id not in existing_ids:
                self._canvas.attachDock(dock)
        for dock_id in list(existing_ids):
            if not any(d.dock_id == dock_id for d in docks):
                self._canvas.removeDock(dock_id)

    def _remove_module_requested(self, dock_id: str) -> None:
        self._viewmodel.remove_module(dock_id)

    def _add_module(self, module_id: str) -> None:
        try:
            dock = self._viewmodel.add_module(module_id)
            self._canvas.attachDock(dock)
        except Exception:
            pass

    def _load_initial_modules(self) -> None:
        state = self._settings.load()
        modules = state.layout_snapshot.get("modules", []) if state.layout_snapshot else []
        if not modules:
            modules = ["stopwatch"]
        self._viewmodel.load_modules(modules)

    def _apply_saved_geometry(self) -> None:
        state = self._settings.load()
        if state.geometry:
            self.restoreGeometry(state.geometry)
        self._btn_on_top.setChecked(state.always_on_top)
        if state.screen_name:
            for idx in range(self._screen_combo.count()):
                screen = self._screen_combo.itemData(idx)
                if isinstance(screen, QtGui.QScreen) and screen.name() == state.screen_name:
                    self._screen_combo.setCurrentIndex(idx)
                    break
            else:
                self._center_on_primary()
        else:
            self._center_on_primary()

    def _center_on_primary(self) -> None:
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen:
            self._move_to_screen(screen)

    def _populate_screens(self) -> None:
        self._screen_combo.clear()
        for screen in QtGui.QGuiApplication.screens():
            text = f"{screen.name()} • {screen.geometry().width()}x{screen.geometry().height()}"
            self._screen_combo.addItem(text, screen)

    def _refresh_module_menu(self) -> None:
        self._module_menu.clear()
        for descriptor in self._viewmodel.registry.list_available():
            action = self._module_menu.addAction(descriptor.title)
            action.triggered.connect(lambda _, mid=descriptor.module_id: self._add_module(mid))

    def save_state(self) -> None:
        self._settings.update_geometry(self.saveGeometry())

    def _schedule_geometry_save(self) -> None:
        timer = getattr(self, "_geometry_timer", None)
        if timer is None:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self.save_state)
            self._geometry_timer = timer
        timer.start(500)

    # endregion


__all__ = ["WidgetHostWindow", "WidgetCanvas"]
