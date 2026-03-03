from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from src.styles.constants import Sizes
from src.utils.translator import tr
from src.views.quick_blocks_model import (
    QuickBlockItemType,
    QuickBlockListItem,
    QuickBlocksListModel,
)


class QuickBlocksDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._padding = Sizes.CARD_MARGIN // 2
        self._spacing = Sizes.LAYOUT_SPACING // 2

    # -- Painting ----------------------------------------------------------
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        data = index.data(QuickBlocksListModel.DATA_ROLE)
        if data is None:
            self._paint_placeholder(painter, option)
            return
        item: QuickBlockListItem = data
        if item.item_type == QuickBlockItemType.GROUP_HEADER:
            self._paint_group_header(painter, option, item)
        elif item.item_type == QuickBlockItemType.BLOCK:
            self._paint_block_row(painter, option, item)
        else:
            self._paint_placeholder(painter, option)

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:  # type: ignore[override]
        data = index.data(QuickBlocksListModel.DATA_ROLE)
        height = Sizes.INPUT_MIN_HEIGHT + self._padding * 2
        if data is None:
            return QtCore.QSize(option.rect.width(), height)
        item: QuickBlockListItem = data
        if item.item_type == QuickBlockItemType.GROUP_HEADER:
            return QtCore.QSize(option.rect.width(), Sizes.INPUT_MIN_HEIGHT)
        return QtCore.QSize(option.rect.width(), height)

    # -- Helpers -----------------------------------------------------------
    def _paint_placeholder(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem) -> None:
        painter.save()
        rect = option.rect.adjusted(self._padding, self._padding, -self._padding, -self._padding)
        color = option.palette.color(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText)
        color.setAlpha(40)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)
        painter.restore()

    def _paint_group_header(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, item: QuickBlockListItem) -> None:
        painter.save()
        rect = option.rect.adjusted(self._padding, 0, -self._padding, 0)
        font = option.font
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(option.palette.color(QtGui.QPalette.Text))
        title = item.group.name if item.group else tr("group", "Group")
        suffix = f" ({len(item.group.blocks) if item.group else 0})"
        painter.drawText(rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, title + suffix)
        arrow = "▼" if not item.is_collapsed else "▶"
        painter.drawText(rect.adjusted(0, 0, -self._padding, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, arrow)
        painter.restore()

    def _paint_block_row(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, item: QuickBlockListItem) -> None:
        painter.save()
        rect = option.rect.adjusted(self._padding, self._padding, -self._padding, -self._padding)
        bg_color = option.palette.window().color()
        if item.is_selected:
            bg_color = option.palette.highlight().color()
        painter.setBrush(bg_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)

        text_rect = rect.adjusted(self._spacing, 0, -self._spacing, 0)
        painter.setPen(option.palette.color(QtGui.QPalette.ButtonText))
        title = item.block.title if item.block else tr("block", "Block")
        painter.drawText(text_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, title)

        painter.restore()
