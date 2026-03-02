"""Quick Blocks panel redesigned with card-style layout."""

from __future__ import annotations

from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from src.styles.constants import Sizes
from src.utils.icon_cache import get_icon_cache
from src.utils.quick_blocks_repository import QuickBlock, QuickBlocksRepository
from src.utils.theme_manager import theme_manager
from src.utils.translator import tr, translator
from src.views.quick_block_editor_dialog import create_block


class BlockRow(QtWidgets.QFrame):
    """Single block row widget built with grid layout."""

    triggered = QtCore.Signal(str, str)
    selected = QtCore.Signal(str)
    context_action = QtCore.Signal(str, str)

    def __init__(self, block: QuickBlock, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.block = block
        self.setObjectName("quick-block-row")
        self._selected = False
        self._indicator_state = "idle"
        self._indicator: QtWidgets.QLabel | None = None
        self.setProperty("selected", False)
        self._shortcuts: list[QtGui.QShortcut] = []
        self.destroyed.connect(self._dispose_shortcuts)

        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(Sizes.CARD_MARGIN // 2, Sizes.CARD_MARGIN // 2, Sizes.CARD_MARGIN // 2 + Sizes.LAYOUT_SPACING // 2, Sizes.CARD_MARGIN // 2)
        grid.setHorizontalSpacing(Sizes.LAYOUT_SPACING // 2)
        grid.setVerticalSpacing(2)

        title_label = QtWidgets.QLabel(block.title)
        title_label.setObjectName("quick-block-title")
        title_label.setCursor(QtCore.Qt.PointingHandCursor)
        title_label.installEventFilter(self)
        grid.addWidget(title_label, 0, 0)

        indicator = QtWidgets.QLabel()
        indicator.setObjectName("quick-block-indicator")
        indicator.setFixedSize(12, 12)
        indicator.setAlignment(QtCore.Qt.AlignCenter)
        indicator.setProperty("blockState", self._indicator_state)
        grid.addWidget(indicator, 0, 1, QtCore.Qt.AlignCenter)
        self._indicator = indicator

        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(Sizes.LAYOUT_SPACING // 3)

        self._btn_on = QtWidgets.QPushButton()
        on_btn = self._btn_on
        on_btn.setProperty("semanticRole", "quick_block_on")
        on_btn.setFixedHeight(Sizes.INPUT_MIN_HEIGHT)
        on_btn.setMinimumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH // 2)
        on_btn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        on_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        on_btn.clicked.connect(lambda: self.triggered.emit(block.id, "on"))
        controls_layout.addWidget(on_btn)

        if block.mode != "single":
            self._btn_off = QtWidgets.QPushButton()
            off_btn = self._btn_off
            off_btn.setProperty("semanticRole", "quick_block_off")
            off_btn.setFixedHeight(Sizes.INPUT_MIN_HEIGHT)
            off_btn.setMinimumWidth(Sizes.BUTTON_SAVE_MAX_WIDTH // 2)
            off_btn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            off_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            off_btn.clicked.connect(lambda: self.triggered.emit(block.id, "off"))
            controls_layout.addWidget(off_btn)
        else:
            self._btn_off = None

        controls.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        grid.addWidget(controls, 0, 2, QtCore.Qt.AlignRight)
        grid.setColumnStretch(0, 1)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._retranslate_controls()
        translator.language_changed.connect(self._on_language_changed)
        self._register_hotkey()

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:  # type: ignore[override]
        if watched.objectName() == "quick-block-title" and event.type() == QtCore.QEvent.MouseButtonPress:
            mouse_event = QtGui.QMouseEvent(event)
            if mouse_event.button() == QtCore.Qt.LeftButton:
                self.selected.emit(self.block.id)
        return super().eventFilter(watched, event)

    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        action_edit = menu.addAction(tr("edit", "Edit"))
        action_duplicate = menu.addAction(tr("duplicate", "Duplicate"))
        action_delete = menu.addAction(tr("delete", "Delete"))
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == action_edit:
            self.context_action.emit(self.block.id, "edit")
        elif chosen == action_duplicate:
            self.context_action.emit(self.block.id, "duplicate")
        elif chosen == action_delete:
            self.context_action.emit(self.block.id, "delete")

    def set_selected(self, is_selected: bool) -> None:
        if self._selected == is_selected:
            return
        self._selected = is_selected
        self.setProperty("selected", is_selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_indicator_state(self, state: str | None) -> None:
        self._indicator_state = state or "idle"
        if self._indicator:
            self._indicator.setProperty("blockState", self._indicator_state)
            self._indicator.style().unpolish(self._indicator)
            self._indicator.style().polish(self._indicator)
            self._indicator.update()

    def _retranslate_controls(self) -> None:
        self._btn_on.setText(tr("quick_block_on", "ON"))
        if self._btn_off:
            self._btn_off.setText(tr("quick_block_off", "OFF"))
        
    def _on_language_changed(self, _: str) -> None:
        self._retranslate_controls()
        self._register_hotkey()

    def _dispose_shortcuts(self) -> None:
        while self._shortcuts:
            shortcut = self._shortcuts.pop()
            try:
                shortcut.activated.disconnect()
            except (RuntimeError, TypeError):
                pass
            shortcut.setParent(None)
            shortcut.deleteLater()

    def dispose(self) -> None:
        self._dispose_shortcuts()

    def _register_hotkey(self) -> None:
        self._dispose_shortcuts()
        hotkey = (self.block.hotkey or "").strip()
        if not hotkey:
            return
        sequence = QtGui.QKeySequence(hotkey)
        if sequence.count() == 0 or sequence[0] == 0:
            return
        shortcut = QtGui.QShortcut(sequence, self)
        shortcut.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
        shortcut.activated.connect(lambda: self.triggered.emit(self.block.id, "on"))
        self._shortcuts.append(shortcut)
        self.setToolTip(tr("quick_block_hotkey_hint", "Hotkey: {key_display}", **{"key_display": sequence.toString()}))



class GroupCard(QtWidgets.QFrame):
    """Card with collapsible list of block rows."""

    block_triggered = QtCore.Signal(str, str)
    block_selected = QtCore.Signal(str)
    collapse_changed = QtCore.Signal(str, bool)
    context_action = QtCore.Signal(str, str)

    def __init__(self, group_id: str, title: str, collapsed: bool, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.group_id = group_id
        self._title = title
        self._block_count = 0
        self._rows: list[BlockRow] = []
        self._selected_block_id: str | None = None
        self._context_handler: QtCore.SignalInstance | None = None
        self.setObjectName("quick-block-card")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN)
        header.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self._toggle = QtWidgets.QToolButton()
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not collapsed)
        self._toggle.setArrowType(QtCore.Qt.DownArrow if not collapsed else QtCore.Qt.RightArrow)
        self._toggle.clicked.connect(self._on_toggle)
        header.addWidget(self._toggle)

        self._title_label = QtWidgets.QLabel()
        self._title_label.setObjectName("quick-block-card-title")
        header.addWidget(self._title_label)
        header.addStretch(1)

        layout.addLayout(header)

        self._body = QtWidgets.QWidget()
        self._body.setObjectName("quick-block-card-body")
        self._body_layout = QtWidgets.QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, Sizes.CARD_MARGIN)
        self._body_layout.setSpacing(1)
        layout.addWidget(self._body)
        self._body.setVisible(not collapsed)

        self._update_title()

    def set_blocks(self, blocks: list[QuickBlock]) -> None:
        self._block_count = len(blocks)
        self._rows.clear()
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if (widget := item.widget()) is not None:
                if isinstance(widget, BlockRow):
                    widget.dispose()
                widget.deleteLater()
        for idx, block in enumerate(blocks):
            row = BlockRow(block)
            row.triggered.connect(partial(self._on_row_triggered, row))
            row.selected.connect(self.block_selected)
            row.context_action.connect(self._on_context_action)
            self._body_layout.addWidget(row)
            self._rows.append(row)
        self._update_title()
        self.set_selected_block(self._selected_block_id)

    def _update_title(self) -> None:
        suffix = f"({self._block_count})"
        self._title_label.setText(f"{self._title} {suffix}")
        expanded = self._toggle.isChecked()
        self._toggle.setArrowType(QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow)

    def set_selected_block(self, block_id: str | None) -> None:
        self._selected_block_id = block_id
        for row in self._rows:
            row.set_selected(row.block.id == block_id)

    def update_block_state(self, block_id: str, state: str | None) -> bool:
        for row in self._rows:
            if row.block.id == block_id:
                row.set_indicator_state(state)
                return True
        return False

    def _on_toggle(self) -> None:
        expanded = self._toggle.isChecked()
        self._body.setVisible(expanded)
        self._update_title()
        self.collapse_changed.emit(self.group_id, not expanded)

    def _on_row_triggered(self, row: BlockRow, block_id: str, action: str) -> None:
        row.set_indicator_state("pending")
        self.block_triggered.emit(block_id, action)

    def _on_context_action(self, block_id: str, action: str) -> None:
        self.block_selected.emit(block_id)
        self.context_action.emit(block_id, action)


class QuickBlocksPanel(QtWidgets.QWidget):
    """Panel that mimics reference card design."""

    block_triggered = QtCore.Signal(str, str)

    def __init__(self, repository: QuickBlocksRepository, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._selected_block: str | None = None
        self._group_cards: list[GroupCard] = []
        self._btn_reload: QtWidgets.QPushButton | None = None
        self._btn_add: QtWidgets.QPushButton | None = None
        self._btn_edit: QtWidgets.QPushButton | None = None
        self._icon_cache = get_icon_cache()

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(Sizes.LAYOUT_MARGIN // 2, 0, Sizes.LAYOUT_MARGIN // 2, 0)
        root.setSpacing(Sizes.LAYOUT_SPACING // 2)

        toolbar = self._create_toolbar()
        root.addLayout(toolbar)

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._content = QtWidgets.QWidget()
        self._content.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self._content_layout = QtWidgets.QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(Sizes.LAYOUT_MARGIN // 2, 0, Sizes.LAYOUT_MARGIN // 2, Sizes.CARD_MARGIN)
        self._content_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self._content_layout.addStretch(1)
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll)

        translator.language_changed.connect(lambda _: self._retranslate_ui())
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.refresh()
        self._retranslate_ui()
        self._update_toolbar_icons()

    def _create_toolbar(self) -> QtWidgets.QHBoxLayout:
        layout = QtWidgets.QHBoxLayout()
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

        return layout

    def _retranslate_ui(self) -> None:
        if self._btn_add:
            self._btn_add.setText(tr("add", "Add"))
        if self._btn_edit:
            self._btn_edit.setText(tr("edit", "Edit"))
        if self._btn_reload:
            self._btn_reload.setText(tr("reload", "Reload"))
        for card in self._group_cards:
            card.update()
        self._update_toolbar_icons()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        if event.type() == QtCore.QEvent.LanguageChange:
            self._retranslate_ui()
        super().changeEvent(event)

    def _on_theme_changed(self, _theme: str) -> None:
        self._update_toolbar_icons()

    def refresh(self) -> None:
        self._group_cards.clear()
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if (widget := item.widget()) is not None:
                widget.deleteLater()

        for group in self._repository.list_groups():
            card = GroupCard(group.id, group.name, group.collapsed)
            card.block_triggered.connect(self.block_triggered)
            card.block_selected.connect(self._on_block_selected)
            card.collapse_changed.connect(self._on_collapse_changed)
            card.context_action.connect(self._on_context_action)
            card.set_blocks(group.blocks)
            if self._selected_block:
                card.set_selected_block(self._selected_block)
            self._content_layout.insertWidget(self._content_layout.count() - 1, card)
            self._group_cards.append(card)

    def _update_toolbar_icons(self) -> None:
        if not self._icon_cache:
            self._icon_cache = get_icon_cache()
        if self._btn_add:
            self._btn_add.setIcon(self._icon_cache.get("paper-plane"))
        if self._btn_edit:
            self._btn_edit.setIcon(self._icon_cache.get("floppy-disk"))
        if self._btn_reload:
            self._btn_reload.setIcon(self._icon_cache.get("clock-rotate-left"))

    def _on_block_selected(self, block_id: str) -> None:
        self._selected_block = block_id
        for card in self._group_cards:
            card.set_selected_block(block_id)

    def _on_collapse_changed(self, group_id: str, collapsed: bool) -> None:
        self._repository.set_group_collapsed(group_id, collapsed)

    def update_block_state(self, block_id: str, state: str | None) -> None:
        for card in self._group_cards:
            if card.update_block_state(block_id, state):
                break

    def _on_context_action(self, block_id: str, action: str) -> None:
        self._selected_block = block_id
        if action == "edit":
            self._on_edit_block()
        elif action == "duplicate":
            self._on_duplicate()
        elif action == "delete":
            self._on_delete()

    # Toolbar actions ---------------------------------------------------
    def _current_block(self) -> QuickBlock | None:
        return self._repository.get_block(self._selected_block) if self._selected_block else None

    def _on_add_block(self) -> None:
        groups = self._repository.list_groups()
        if not groups:
            QtWidgets.QMessageBox.warning(self, self.windowTitle(), tr("no_groups", "Create a group first"))
            return
        block = create_block(self, groups=groups)
        if block:
            self._repository.add_block(block)
            self.refresh()

    def _on_edit_block(self) -> None:
        block = self._current_block()
        if not block:
            return
        groups = self._repository.list_groups()
        updated = create_block(self, groups=groups, block=block)
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
