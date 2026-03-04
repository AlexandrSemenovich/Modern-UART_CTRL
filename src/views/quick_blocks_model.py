from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, List

from PySide6 import QtCore

from src.utils.quick_blocks_repository import QuickBlock, QuickBlocksRepository, QuickGroup


class QuickBlockItemType(Enum):
    GROUP_HEADER = auto()
    BLOCK = auto()
    PLACEHOLDER = auto()


@dataclass(slots=True)
class QuickBlockListItem:
    item_type: QuickBlockItemType
    group: QuickGroup | None = None
    block: QuickBlock | None = None
    is_collapsed: bool = False
    is_selected: bool = False
    indicator_state: str | None = None


class QuickBlocksListModel(QtCore.QAbstractListModel):
    block_triggered = QtCore.Signal(str, str)
    block_selected = QtCore.Signal(str)
    context_action = QtCore.Signal(str, str)
    collapse_changed = QtCore.Signal(str, bool)

    TYPE_ROLE = QtCore.Qt.UserRole + 1
    DATA_ROLE = QtCore.Qt.UserRole + 2

    def __init__(self, repository: QuickBlocksRepository, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._items: List[QuickBlockListItem] = []
        self._skeleton_count = 0

    # -- Qt model overrides -------------------------------------------------
    def rowCount(self, parent: QtCore.QModelIndex | None = None) -> int:  # type: ignore[override]
        if parent and parent.isValid():
            return 0
        count = len(self._items)
        if self._skeleton_count:
            count += self._skeleton_count
        return count

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row >= len(self._items):
            if role == self.TYPE_ROLE:
                return QuickBlockItemType.PLACEHOLDER
            return None
        item = self._items[row]
        if role == self.TYPE_ROLE:
            return item.item_type
        if role == self.DATA_ROLE:
            return item
        return None

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:  # type: ignore[override]
        base = super().flags(index)
        if not index.isValid() or index.row() >= len(self._items):
            return base
        item = self._items[index.row()]
        if item.item_type == QuickBlockItemType.GROUP_HEADER:
            return base | QtCore.Qt.ItemIsEnabled
        if item.item_type == QuickBlockItemType.BLOCK:
            return base | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return base

    # -- Public API ---------------------------------------------------------
    def show_skeleton(self, count: int = 6) -> None:
        if self._items:
            return
        if self._skeleton_count == count:
            return
        self.beginResetModel()
        self._skeleton_count = count
        self.endResetModel()

    def hide_skeleton(self) -> None:
        if not self._skeleton_count:
            return
        self.beginResetModel()
        self._skeleton_count = 0
        self.endResetModel()

    def refresh(self) -> None:
        groups = self._repository.list_groups()
        new_items: List[QuickBlockListItem] = []
        for group in groups:
            new_items.append(
                QuickBlockListItem(
                    item_type=QuickBlockItemType.GROUP_HEADER,
                    group=group,
                    is_collapsed=group.collapsed,
                )
            )
            if group.collapsed:
                continue
            for block in group.blocks:
                new_items.append(
                    QuickBlockListItem(
                        item_type=QuickBlockItemType.BLOCK,
                        group=group,
                        block=block,
                        indicator_state="idle",
                    )
                )

        self.beginResetModel()
        self._items = new_items
        previous_skeleton = self._skeleton_count
        self._skeleton_count = 0
        self.endResetModel()
        if previous_skeleton:
            self.dataChanged.emit(self.index(0), self.index(max(0, len(new_items) - 1)), [self.TYPE_ROLE])

    def has_real_data(self) -> bool:
        """Return True if the model currently holds real Quick Block items."""
        return bool(self._items)

    def set_selected_block(self, block_id: str | None) -> None:
        indexes = [idx for idx, item in enumerate(self._items) if item.item_type == QuickBlockItemType.BLOCK]
        changed: list[int] = []
        for idx in indexes:
            block = self._items[idx].block
            is_selected = block is not None and block.id == block_id
            if self._items[idx].is_selected != is_selected:
                self._items[idx].is_selected = is_selected
                changed.append(idx)
        for idx in changed:
            model_index = self.index(idx)
            self.dataChanged.emit(model_index, model_index, [self.DATA_ROLE])

    def update_indicator(self, block_id: str, state: str | None) -> None:
        for idx, item in enumerate(self._items):
            if item.block and item.block.id == block_id:
                if item.indicator_state == state:
                    return
                item.indicator_state = state
                model_index = self.index(idx)
                self.dataChanged.emit(model_index, model_index, [self.DATA_ROLE])
                return

    def toggle_group(self, group_id: str) -> None:
        for idx, item in enumerate(self._items):
            if item.item_type == QuickBlockItemType.GROUP_HEADER and item.group and item.group.id == group_id:
                collapsed = not item.is_collapsed
                item.is_collapsed = collapsed
                self.collapse_changed.emit(group_id, collapsed)
                self.refresh()
                return

    def find_block_index(self, block_id: str) -> QtCore.QModelIndex | None:
        for idx, item in enumerate(self._items):
            if item.block and item.block.id == block_id:
                return self.index(idx)
        return None

    def list_blocks(self) -> Iterable[QuickBlock]:
        for item in self._items:
            if item.block:
                yield item.block

