"""Virtualized Quick Blocks panel powered by QListView."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from src.styles.constants import Sizes
from src.utils.config_loader import config_loader
from src.utils.icon_cache import get_icon_cache
from src.utils.quick_blocks_repository import QuickBlock, QuickBlocksRepository
from src.utils.theme_manager import theme_manager
from src.utils.translator import tr, translator
from src.views.quick_block_editor_dialog import QuickBlockEditorDialog
from src.views.quick_blocks_delegate import QuickBlocksDelegate
from src.views.quick_blocks_model import (
    QuickBlockItemType,
    QuickBlockListItem,
    QuickBlocksListModel,
)
from src.views.widgets import SkeletonPanelPlaceholder


class QuickBlocksPanel(QtWidgets.QWidget):
    """Virtualized panel that renders Quick Blocks through QListView."""

    block_triggered = QtCore.Signal(str, str)

    def __init__(self, repository: QuickBlocksRepository, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._selected_block: str | None = None
        self._icon_cache = get_icon_cache()
        self._btn_reload: QtWidgets.QPushButton | None = None
        self._btn_add: QtWidgets.QPushButton | None = None
        self._btn_edit: QtWidgets.QPushButton | None = None
        self._shortcut_dispatcher: _QuickBlockShortcutDispatcher | None = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(Sizes.LAYOUT_MARGIN // 2, 0, Sizes.LAYOUT_MARGIN // 2, 0)
        root.setSpacing(Sizes.LAYOUT_SPACING // 2)

        self._toolbar_breakpoint_compact = 480
        self._toolbar_breakpoint_ultra = 320
        self._toolbar_text_mode = "full"
        self._toolbar_labels: dict[str, tuple[str, str]] = {}
        self._toolbar_container = self._create_toolbar()
        root.addWidget(self._toolbar_container)

        self._list_view = QtWidgets.QListView()
        self._list_view.setObjectName("quick_blocks_view")
        self._list_view.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self._list_view.setUniformItemSizes(True)
        self._list_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._list_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._list_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._list_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        root.addWidget(self._list_view, 1)

        self._model = QuickBlocksListModel(repository)
        self._list_view.setModel(self._model)
        self._delegate = QuickBlocksDelegate(self._trigger_block, self._list_view)
        self._list_view.setItemDelegate(self._delegate)
        self._list_view.setUniformItemSizes(False)

        self._list_view.clicked.connect(self._on_item_clicked)
        self._list_view.doubleClicked.connect(self._on_item_double_clicked)
        self._list_view.customContextMenuRequested.connect(self._show_context_menu)

        translator.language_changed.connect(lambda _: self._retranslate_ui())
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._model.collapse_changed.connect(self._on_collapse_changed)

        self._model.show_skeleton()
        QtCore.QTimer.singleShot(0, self.refresh)
        self._retranslate_ui()
        self._update_toolbar_icons()
        self._update_toolbar_responsive_class(force=True)

        # Skeleton placeholder until data arrives
        self._skeleton_placeholder = SkeletonPanelPlaceholder()
        root.addWidget(self._skeleton_placeholder)
        self._update_skeleton_visibility()

        self._shortcut_dispatcher = _QuickBlockShortcutDispatcher(self)
        self._shortcut_dispatcher.rebuild()

    def cleanup(self) -> None:
        if self._shortcut_dispatcher:
            self._shortcut_dispatcher.cleanup()

    # -- UI helpers --------------------------------------------------------
    def _create_toolbar(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        container.setObjectName("quick_blocks_toolbar_container")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(Sizes.TOOLBAR_MARGIN, 0, Sizes.TOOLBAR_MARGIN, 0)
        layout.setSpacing(Sizes.TOOLBAR_SPACING)

        layout.addStretch(1)

        self._btn_add = QtWidgets.QPushButton()
        self._btn_add.setProperty("semanticRole", "quick_toolbar_action")
        self._btn_add.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._btn_add.clicked.connect(self._on_add_block)
        layout.addWidget(self._btn_add)

        self._btn_edit = QtWidgets.QPushButton()
        self._btn_edit.setProperty("semanticRole", "quick_toolbar_action")
        self._btn_edit.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._btn_edit.clicked.connect(self._on_edit_block)
        layout.addWidget(self._btn_edit)

        self._btn_reload = QtWidgets.QPushButton()
        self._btn_reload.setProperty("semanticRole", "quick_toolbar_action")
        self._btn_reload.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._btn_reload.clicked.connect(self._on_reload)
        layout.addWidget(self._btn_reload)

        layout.addStretch(1)
        return container

    def _update_toolbar_responsive_class(self, *, force: bool = False) -> None:
        if not hasattr(self, '_toolbar_container') or not self._toolbar_container:
            return
        width = self.width()
        if width <= 0:
            return

        compact_breakpoint = self._toolbar_breakpoint_compact
        ultra_breakpoint = self._toolbar_breakpoint_ultra

        if width <= ultra_breakpoint:
            target = "ultra-compact"
        elif width <= compact_breakpoint:
            target = "compact"
        else:
            target = ""

        current = self._toolbar_container.property("sizeClass") or ""
        if not force and current == target:
            return

        self._toolbar_container.setProperty("sizeClass", target)
        classes = set(filter(None, str(self._toolbar_container.property("class") or "").split()))
        classes.discard("compact")
        classes.discard("ultra-compact")
        if target:
            classes.add(target)
        self._toolbar_container.setProperty("class", " ".join(sorted(classes)))
        self._refresh_widget_style(self._toolbar_container)
        self._apply_toolbar_text_mode(target)

    def _apply_toolbar_text_mode(self, size_class: str, *, force: bool = False) -> None:
        mode = "icons"
        if size_class == "compact":
            mode = "labels"
        elif size_class == "":
            mode = "full"

        if not force and self._toolbar_text_mode == mode and self._toolbar_labels:
            return
        self._toolbar_text_mode = mode

        for button, key in (
            (self._btn_add, "add"),
            (self._btn_edit, "edit"),
            (self._btn_reload, "reload"),
        ):
            if not button:
                continue
            full_text, short_text = self._toolbar_labels.get(key, ("", ""))
            if mode == "full":
                button.setText(full_text)
            elif mode == "labels":
                button.setText(short_text or full_text)
            else:
                button.setText("")
            button.setToolTip(full_text)
            button.setAccessibleName(full_text)

    def _retranslate_ui(self) -> None:
        self._toolbar_labels = {
            "add": (tr("add_block", "Add block"), tr("add", "Add")),
            "edit": (tr("edit_block", "Edit block"), tr("edit", "Edit")),
            "reload": (tr("reload_quick_blocks", "Reload blocks"), tr("reload", "Reload")),
        }

        for key, button in (("add", self._btn_add), ("edit", self._btn_edit), ("reload", self._btn_reload)):
            if not button:
                continue
            full_text, _ = self._toolbar_labels[key]
            button.setToolTip(full_text)

        size_class = ""
        if hasattr(self, "_toolbar_container") and self._toolbar_container:
            size_class = self._toolbar_container.property("sizeClass") or ""
        self._apply_toolbar_text_mode(size_class, force=True)
        self._update_toolbar_icons()

    def _refresh_widget_style(self, widget: QtWidgets.QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def changeEvent(self, event: QtCore.QEvent) -> None:  # type: ignore[override]
        if event.type() == QtCore.QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def _on_theme_changed(self, _theme: str) -> None:
        self._update_toolbar_icons()

    def _update_toolbar_icons(self) -> None:
        if not self._icon_cache:
            self._icon_cache = get_icon_cache()
        if self._btn_add:
            self._btn_add.setIcon(self._icon_cache.get("paper-plane"))
        if self._btn_edit:
            self._btn_edit.setIcon(self._icon_cache.get("floppy-disk"))
        if self._btn_reload:
            self._btn_reload.setIcon(self._icon_cache.get("clock-rotate-left"))

    # -- Model interaction -------------------------------------------------
    def refresh(self) -> None:
        self._model.refresh()
        if self._selected_block:
            self._model.set_selected_block(self._selected_block)
        self._list_view.reset()
        if self._shortcut_dispatcher:
            self._shortcut_dispatcher.rebuild()
        self._update_skeleton_visibility()

    def _update_skeleton_visibility(self) -> None:
        has_data = self._model.has_real_data()
        if getattr(self, "_skeleton_placeholder", None):
            self._skeleton_placeholder.setVisible(not has_data)
        self._list_view.setVisible(has_data)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_toolbar_responsive_class()

    def update_block_state(self, block_id: str, state: str | None) -> None:
        self._model.update_indicator(block_id, state)
        
    def _on_item_clicked(self, index: QtCore.QModelIndex) -> None:
        item_type = index.data(QuickBlocksListModel.TYPE_ROLE)
        item: QuickBlockListItem | None = index.data(QuickBlocksListModel.DATA_ROLE)
        if item is None:
            return
        if item_type == QuickBlockItemType.GROUP_HEADER and item.group:
            self._model.toggle_group(item.group.id)
            return
        if item_type == QuickBlockItemType.BLOCK and item.block:
            self._select_block(item.block.id)

    def _on_item_double_clicked(self, index: QtCore.QModelIndex) -> None:
        item: QuickBlockListItem | None = index.data(QuickBlocksListModel.DATA_ROLE)
        if not item or not item.block:
            return
        self._select_block(item.block.id)
        self._trigger_block(item.block.id, "on")

    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        index = self._list_view.indexAt(pos)
        if not index.isValid():
            return
        item: QuickBlockListItem | None = index.data(QuickBlocksListModel.DATA_ROLE)
        if not item or not item.block:
            return
        block = item.block
        menu = QtWidgets.QMenu(self)
        action_run_on = menu.addAction(tr("quick_block_on", "Run ON"))
        action_run_off = None
        if block.mode != "single":
            action_run_off = menu.addAction(tr("quick_block_off", "Run OFF"))
        menu.addSeparator()
        action_edit = menu.addAction(tr("edit", "Edit"))
        action_duplicate = menu.addAction(tr("duplicate", "Duplicate"))
        action_delete = menu.addAction(tr("delete", "Delete"))
        menu.addSeparator()
        action_hotkey_assign = menu.addAction(tr("assign_hotkey", "Assign Hotkey"))
        action_hotkey_clear = menu.addAction(tr("clear_hotkey", "Clear Hotkey"))
        chosen = menu.exec(self._list_view.viewport().mapToGlobal(pos))
        if chosen == action_run_on:
            self._trigger_block(block.id, "on")
        elif chosen == action_run_off:
            self._trigger_block(block.id, "off")
        elif chosen == action_edit:
            self._selected_block = block.id
            self._on_edit_block()
        elif chosen == action_duplicate:
            self._selected_block = block.id
            self._on_duplicate()
        elif chosen == action_delete:
            self._selected_block = block.id
            self._on_delete()
        elif chosen == action_hotkey_assign:
            self._selected_block = block.id
            self._on_assign_hotkey()
        elif chosen == action_hotkey_clear:
            self._selected_block = block.id
            self._clear_hotkey(block)

    def _trigger_block(self, block_id: str, action: str) -> None:
        self._model.update_indicator(block_id, "pending")
        self.block_triggered.emit(block_id, action)

    def _select_block(self, block_id: str) -> None:
        if self._selected_block == block_id:
            return
        self._selected_block = block_id
        self._model.set_selected_block(block_id)

    def _on_collapse_changed(self, group_id: str, collapsed: bool) -> None:
        self._repository.set_group_collapsed(group_id, collapsed)

    # -- Toolbar actions ---------------------------------------------------
    def _current_block(self) -> QuickBlock | None:
        return self._repository.get_block(self._selected_block) if self._selected_block else None

    def _on_add_block(self) -> None:
        groups = self._repository.list_groups()
        if not groups:
            QtWidgets.QMessageBox.warning(self, self.windowTitle(), tr("no_groups", "Create a group first"))
            return
        block = self._open_editor(groups=groups)
        if block:
            self._repository.add_block(block)
            self.refresh()

    def _on_edit_block(self) -> None:
        block = self._current_block()
        if not block:
            return
        groups = self._repository.list_groups()
        updated = self._open_editor(groups=groups, block=block)
        if updated:
            self._repository.update_block(updated)
            self.refresh()

    def _on_delete(self) -> None:
        block = self._current_block()
        if not block:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            tr("delete_block", "Delete block"),
            tr("confirm_delete_block", "Delete selected block?"),
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self._repository.remove_block(block.id)
            self.refresh()
            if self._shortcut_dispatcher:
                self._shortcut_dispatcher.rebuild()

    def _on_duplicate(self) -> None:
        block = self._current_block()
        if not block:
            return
        clone = QuickBlock(
            id=QtCore.QUuid.createUuid().toString(QtCore.QUuid.Id128)[1:-1],
            title=f"{block.title} Copy",
            command_on=block.command_on,
            command_off=block.command_off,
            send_to_combo=block.send_to_combo,
            group_id=block.group_id,
            order=block.order + 1,
            mode=block.mode,
            icon=block.icon,
            port=block.port,
            hotkey=None,
        )
        self._repository.add_block(clone)
        self.refresh()
        if self._shortcut_dispatcher:
            self._shortcut_dispatcher.rebuild()

    def _on_reload(self) -> None:
        confirm = QtWidgets.QMessageBox.question(
            self,
            tr("reload", "Reload"),
            tr("confirm_reload", "Reload configuration from file? Unsaved changes will be lost."),
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self._repository.reload()
            self.refresh()
            self._flash_reload_button()
            if self._shortcut_dispatcher:
                self._shortcut_dispatcher.rebuild(reset_overrides=True)

    def _open_editor(self, *, groups: list, block: QuickBlock | None = None) -> QuickBlock | None:
        dialog = QuickBlockEditorDialog(self, groups=groups, block=block)
        dialog.set_hotkey_validator(self._validate_hotkey)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            return dialog.result_block()
        return None

    def _validate_hotkey(self, sequence: str | None, exclude_id: str | None) -> tuple[bool, str]:
        cleaned = (sequence or "").strip()
        if not cleaned:
            return True, ""
        normalized = cleaned.lower()
        for group in self._repository.list_groups():
            for block in group.blocks:
                if exclude_id and block.id == exclude_id:
                    continue
                if (block.hotkey or "").strip().lower() == normalized:
                    return False, tr("hotkey_conflict_message", "Hotkey {sequence} is already used.").format(sequence=cleaned)
        return True, ""

    def _on_assign_hotkey(self) -> None:
        block = self._current_block()
        if not block:
            return
        groups = self._repository.list_groups()
        block_clone = QuickBlock(
            id=block.id,
            title=block.title,
            command_on=block.command_on,
            command_off=block.command_off,
            send_to_combo=block.send_to_combo,
            group_id=block.group_id,
            order=block.order,
            mode=block.mode,
            icon=block.icon,
            port=block.port,
            hotkey=block.hotkey,
        )
        dialog = QuickBlockEditorDialog(self, groups=groups, block=block_clone)
        dialog.set_hotkey_validator(self._validate_hotkey)
        dialog._title_edit.setReadOnly(True)
        dialog._group_combo.setEnabled(False)
        dialog._port_combo.setEnabled(False)
        dialog._command_on.setReadOnly(True)
        dialog._command_off.setReadOnly(True)
        dialog._mode_checkbox.setEnabled(False)
        dialog._send_combo_chk.setEnabled(False)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        updated = dialog.result_block()
        block.hotkey = updated.hotkey
        self._repository.update_block(block)
        self.refresh()
        if self._shortcut_dispatcher:
            self._shortcut_dispatcher.rebuild()

    def _clear_hotkey(self, block: QuickBlock) -> None:
        if not block.hotkey:
            return
        block.hotkey = None
        self._repository.update_block(block)
        self.refresh()
        if self._shortcut_dispatcher:
            self._shortcut_dispatcher.rebuild()

    def _flash_reload_button(self) -> None:
        if not self._btn_reload:
            return
        self._btn_reload.setProperty("flashState", "active")
        self._btn_reload.style().unpolish(self._btn_reload)
        self._btn_reload.style().polish(self._btn_reload)
        QtCore.QTimer.singleShot(300, self._clear_reload_flash)

    def _clear_reload_flash(self) -> None:
        if not self._btn_reload:
            return
        self._btn_reload.setProperty("flashState", "")
        self._btn_reload.style().unpolish(self._btn_reload)
        self._btn_reload.style().polish(self._btn_reload)

class _QuickBlockShortcutDispatcher(QtCore.QObject):
    def __init__(self, panel: QuickBlocksPanel) -> None:
        super().__init__(panel)
        self._panel = panel
        self._shortcuts: list[QtWidgets.QShortcut] = []
        self._overrides: dict[str, str] = {}
        self._default_shortcuts = config_loader.get_quick_block_shortcuts()

    def cleanup(self) -> None:
        for shortcut in self._shortcuts:
            try:
                shortcut.activated.disconnect()
            except TypeError:
                pass
            shortcut.deleteLater()
        self._shortcuts.clear()

    def rebuild(self, reset_overrides: bool = False) -> None:
        self.cleanup()
        if reset_overrides:
            self._overrides.clear()

        blocks = list(self._panel._model.list_blocks())
        used_sequences: set[str] = set()
        for block in blocks:
            sequence = self._resolve_shortcut(block)
            if not sequence or sequence in used_sequences:
                continue
            used_sequences.add(sequence)
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(sequence), self._panel)
            shortcut.activated.connect(lambda _, bid=block.id: self._panel._trigger_block(bid, "on"))
            self._shortcuts.append(shortcut)

    def _resolve_shortcut(self, block: QuickBlock) -> str | None:
        if block.hotkey:
            return block.hotkey
        port_key = (block.port or "").lower() or "cpu1"
        return self._default_shortcuts.get(port_key)
