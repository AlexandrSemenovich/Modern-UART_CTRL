"""Quick Blocks panel redesigned with card-style layout."""

from __future__ import annotations

from functools import partial

from PySide6 import QtCore, QtWidgets

from src.styles.constants import Sizes
from src.utils.quick_blocks_repository import QuickBlock, QuickBlocksRepository
from src.utils.translator import tr
from src.views.quick_block_editor_dialog import create_block


class BlockRow(QtWidgets.QFrame):
    """Single block row widget built with grid layout."""

    triggered = QtCore.Signal(str, str)
    selected = QtCore.Signal(str)

    def __init__(self, block: QuickBlock, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.block = block
        self.setObjectName("quick-block-row")

        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(Sizes.CARD_MARGIN // 2, Sizes.CARD_MARGIN // 2, Sizes.CARD_MARGIN // 2 + 6, Sizes.CARD_MARGIN // 2)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(2)

        title_btn = QtWidgets.QPushButton(f"\uf0c1  {block.title}")
        title_btn.setProperty("semanticRole", "quick_block_title")
        title_btn.setFlat(True)
        title_btn.setCursor(QtCore.Qt.PointingHandCursor)
        title_btn.clicked.connect(lambda: self.selected.emit(block.id))
        title_btn.setFixedHeight(Sizes.INPUT_MIN_HEIGHT)
        title_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        grid.addWidget(title_btn, 0, 0)

        indicator = QtWidgets.QLabel()
        indicator.setObjectName("quick-block-indicator")
        indicator.setFixedSize(12, 12)
        indicator.setAlignment(QtCore.Qt.AlignCenter)
        grid.addWidget(indicator, 0, 1, QtCore.Qt.AlignCenter)

        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)

        on_btn = QtWidgets.QPushButton("ON")
        on_btn.setProperty("semanticRole", "quick_block_on")
        on_btn.setFixedHeight(Sizes.INPUT_MIN_HEIGHT)
        on_btn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        on_btn.clicked.connect(lambda: self.triggered.emit(block.id, "on"))
        controls_layout.addWidget(on_btn)

        if block.mode != "single":
            off_btn = QtWidgets.QPushButton("OFF")
            off_btn.setProperty("semanticRole", "quick_block_off")
            off_btn.setFixedHeight(Sizes.INPUT_MIN_HEIGHT)
            off_btn.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
            off_btn.clicked.connect(lambda: self.triggered.emit(block.id, "off"))
            controls_layout.addWidget(off_btn)

        controls.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        grid.addWidget(controls, 0, 2, QtCore.Qt.AlignRight)
        grid.setColumnStretch(0, 1)



class GroupCard(QtWidgets.QFrame):
    """Card with collapsible list of block rows."""

    block_triggered = QtCore.Signal(str, str)
    block_selected = QtCore.Signal(str)
    collapse_changed = QtCore.Signal(str, bool)

    def __init__(self, group_id: str, title: str, collapsed: bool, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.group_id = group_id
        self.setObjectName("quick-block-card")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN, Sizes.CARD_MARGIN)
        self._toggle = QtWidgets.QToolButton()
        self._toggle.setCheckable(True)
        self._toggle.setChecked(not collapsed)
        self._toggle.setText(self._text_for_state(not collapsed, title))
        self._toggle.clicked.connect(partial(self._on_toggle, title))
        header.addWidget(self._toggle)
        header.addStretch(1)
        layout.addLayout(header)

        self._body = QtWidgets.QWidget()
        self._body.setObjectName("quick-block-card-body")
        self._body_layout = QtWidgets.QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, Sizes.CARD_MARGIN)
        self._body_layout.setSpacing(1)
        layout.addWidget(self._body)
        self._body.setVisible(not collapsed)

    def set_blocks(self, blocks: list[QuickBlock]) -> None:
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if (widget := item.widget()) is not None:
                widget.deleteLater()
        for idx, block in enumerate(blocks):
            row = BlockRow(block)
            row.triggered.connect(self.block_triggered)
            row.selected.connect(self.block_selected)
            self._body_layout.addWidget(row)
            if idx != len(blocks) - 1:
                divider = QtWidgets.QFrame()
                divider.setFrameShape(QtWidgets.QFrame.HLine)
                divider.setObjectName("quick-block-divider")
                divider.setFixedHeight(1)
                self._body_layout.addWidget(divider)

    def _on_toggle(self, title: str) -> None:
        expanded = self._toggle.isChecked()
        self._toggle.setText(self._text_for_state(expanded, title))
        self._body.setVisible(expanded)
        self.collapse_changed.emit(self.group_id, not expanded)

    @staticmethod
    def _text_for_state(expanded: bool, title: str) -> str:
        symbol = "[-]" if expanded else "[+]"
        return f"{symbol} {title}"


class QuickBlocksPanel(QtWidgets.QWidget):
    """Panel that mimics reference card design."""

    block_triggered = QtCore.Signal(str, str)

    def __init__(self, repository: QuickBlocksRepository, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._selected_block: str | None = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Sizes.LAYOUT_SPACING // 2)

        toolbar = self._create_toolbar()
        root.addLayout(toolbar)

        self._content_container = QtWidgets.QWidget()
        self._content_container.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._content = QtWidgets.QWidget(self._content_container)
        self._content_layout = QtWidgets.QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 8, 0)
        self._content_layout.setSpacing(Sizes.LAYOUT_SPACING // 2)
        self._content_layout.addStretch(1)
        container_layout = QtWidgets.QVBoxLayout(self._content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self._content)
        root.addWidget(self._content_container, 1)

        self.refresh()

    def _create_toolbar(self) -> QtWidgets.QVBoxLayout:
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(4)

        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(4)
        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(4)

        btn_add = QtWidgets.QPushButton(tr("add", "Add"))
        btn_add.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        btn_add.clicked.connect(self._on_add_block)
        row1.addWidget(btn_add)

        btn_edit = QtWidgets.QPushButton(tr("edit", "Edit"))
        btn_edit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        btn_edit.clicked.connect(self._on_edit_block)
        row1.addWidget(btn_edit)

        btn_more = QtWidgets.QPushButton(tr("more_actions", "More"))
        btn_more.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        menu = QtWidgets.QMenu(btn_more)
        action_delete = menu.addAction(tr("delete", "Delete"))
        action_delete.triggered.connect(self._on_delete)
        action_duplicate = menu.addAction(tr("duplicate", "Duplicate"))
        action_duplicate.triggered.connect(self._on_duplicate)
        action_reload = menu.addAction(tr("reload", "Reload"))
        action_reload.triggered.connect(self._on_reload)
        btn_more.setMenu(menu)
        row1.addWidget(btn_more)

        row1.addStretch(1)

        layout.addLayout(row1)
        layout.addLayout(row2)
        return layout

    def refresh(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if (widget := item.widget()) is not None:
                widget.deleteLater()

        for group in self._repository.list_groups():
            card = GroupCard(group.id, group.name, group.collapsed)
            card.block_triggered.connect(self.block_triggered)
            card.block_selected.connect(self._on_block_selected)
            card.collapse_changed.connect(self._on_collapse_changed)
            card.set_blocks(group.blocks)
            self._content_layout.insertWidget(self._content_layout.count() - 1, card)

    def _on_block_selected(self, block_id: str) -> None:
        self._selected_block = block_id

    def _on_collapse_changed(self, group_id: str, collapsed: bool) -> None:
        self._repository.set_group_collapsed(group_id, collapsed)

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
