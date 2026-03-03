from __future__ import annotations

from typing import List

from PySide6 import QtCore

from src.utils.quick_blocks_repository import QuickBlocksRepository, QuickBlock, QuickGroup


class QuickBlockDescriptor(QtCore.QObject):
    def __init__(self, group: QuickGroup, block: QuickBlock, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.group = group
        self.block = block


class QuickBlocksListModel(QtCore.QAbstractListModel):
    block_triggered = QtCore.Signal(str, str)
    block_selected = QtCore.Signal(str)
    context_action = QtCore.Signal(str, str)
    collapse_changed = QtCore.Signal(str, bool)

    def __init__(self, repository: QuickBlocksRepository, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._items: List[QuickBlockDescriptor] = []

    def rowCount(self, parent: QtCore.QModelIndex | None = None) -> int:
        if parent and parent.isValid():
            return 0
        return len(self._items)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.UserRole:
            return self._items[index.row()]
        return None

    def refresh(self) -> None:
        groups = self._repository.list_groups()
        records: List[QuickBlockDescriptor] = []
        for group in groups:
            for block in group.blocks:
                records.append(QuickBlockDescriptor(group, block, self))

        self.beginResetModel()
        self._items = records
        self.endResetModel()
