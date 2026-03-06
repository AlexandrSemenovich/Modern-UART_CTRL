from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from src.styles.constants import Colors, Fonts, Sizes
from src.utils.translator import tr
from src.views.quick_blocks_model import (
    QuickBlockItemType,
    QuickBlockListItem,
    QuickBlocksListModel,
)


class QuickBlocksDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(
        self,
        trigger_callback,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._padding = Sizes.CARD_MARGIN
        self._spacing = Sizes.LAYOUT_SPACING
        self._hit_areas: dict[int, dict[str, QtCore.QRect]] = {}
        self._trigger_callback = trigger_callback
        self._theme_colors = Colors()
        self._button_templates = {
            "on": self._create_button_widget("quick_block_on"),
            "off": self._create_button_widget("quick_block_off"),
        }

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
            self._paint_block_row(painter, option, item, index)
        else:
            self._paint_placeholder(painter, option)

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:  # type: ignore[override]
        data = index.data(QuickBlocksListModel.DATA_ROLE)
        base_height = max(Sizes.BUTTON_MIN_HEIGHT, Sizes.INPUT_MIN_HEIGHT)
        height = base_height + self._padding * 2 + self._spacing
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

    def _paint_block_row(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        item: QuickBlockListItem,
        index: QtCore.QModelIndex,
    ) -> None:
        painter.save()
        effective_theme = "light" if option.palette.color(QtGui.QPalette.Base).lightness() > 128 else "dark"
        theme_colors = self._theme_colors.get_theme_colors(effective_theme)
        palette = option.palette
        base_color = palette.color(QtGui.QPalette.Base)
        hover = bool(option.state & QtWidgets.QStyle.State_MouseOver)
        selected = bool(option.state & QtWidgets.QStyle.State_Selected)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        container_rect = option.rect.adjusted(self._padding, self._padding, -self._padding, -self._padding)
        bg_color = palette.color(QtGui.QPalette.Window)
        border_color = palette.color(QtGui.QPalette.Mid)
        if hover:
            bg_color = bg_color.lighter(104)
        if selected:
            border_color = palette.color(QtGui.QPalette.Highlight)
        painter.setBrush(bg_color)
        painter.setPen(border_color)
        corner_radius = 12
        painter.drawRoundedRect(container_rect, corner_radius, corner_radius)

        content_rect = container_rect.adjusted(self._spacing, self._spacing, -self._spacing, -self._spacing)
        button_count = 2 if item.block and item.block.mode != "single" else 1
        button_width = 84
        button_height = max(Sizes.BUTTON_MIN_HEIGHT, content_rect.height() - self._spacing)
        actions_width = button_count * button_width + (button_count - 1) * self._spacing
        actions_left = content_rect.right() - actions_width - self._spacing
        if actions_left < content_rect.left() + 160:
            actions_left = content_rect.left() + 160

        status_area_right = actions_left - self._spacing
        min_status_width = 90
        max_status_width = 130
        available_status_width = status_area_right - (content_rect.left() + 80)
        if available_status_width < min_status_width:
            available_status_width = min_status_width
        status_width = min(max_status_width, available_status_width)
        status_area_left = status_area_right - status_width
        if status_area_left <= content_rect.left() + 50:
            status_area_left = content_rect.left() + 50
            status_width = status_area_right - status_area_left
        title_rect = QtCore.QRect(content_rect)
        title_rect.setLeft(content_rect.left() + 4)
        title_rect.setRight(max(status_area_left - self._spacing, content_rect.left()))
        title_rect.setTop(content_rect.top())
        title_rect.setBottom(content_rect.bottom())
        painter.setPen(palette.color(QtGui.QPalette.Text))
        title = item.block.title if item.block else tr("block", "Block")
        painter.drawText(title_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, title)

        indicator_size = 12
        indicator_rect = QtCore.QRect(status_area_left, content_rect.center().y() - indicator_size // 2, indicator_size, indicator_size)
        state = (item.indicator_state or "idle").lower()
        color_map = {
            "idle": ("#b0b8c5", tr("quick_block_idle", "Idle")),
            "all_sent": ("#2ecc71", tr("quick_block_success", "Sent")),
            "partial": ("#f1c40f", tr("quick_block_partial", "Partial")),
            "failed": ("#e74c3c", tr("quick_block_failed", "Failed")),
            "pending": ("#b0b8c5", tr("quick_block_pending", "Pending")),
        }
        indicator_color, indicator_text = color_map.get(state, (palette.color(QtGui.QPalette.Mid).name(), state.title()))
        painter.setBrush(QtGui.QColor(indicator_color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(indicator_rect)
        painter.setPen(palette.color(QtGui.QPalette.Text))
        badge_rect = QtCore.QRect(indicator_rect.right() + 6,
                                  content_rect.center().y() - indicator_size,
                                  max(0, status_area_right - self._spacing - (indicator_rect.right() + 6)),
                                  indicator_size * 2)
        painter.drawText(badge_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, indicator_text)

        top_offset = content_rect.top() + (content_rect.height() - button_height) // 2
        on_rect = QtCore.QRect(actions_left,
                               top_offset,
                               button_width,
                               button_height)
        self._draw_button(
            painter,
            on_rect,
            tr("quick_block_on", "ON"),
            role="on",
            enabled=item.block is not None,
            hovered=hover,
            selected=selected,
            palette=palette,
        )

        off_rect = None
        if item.block and item.block.mode != "single":
            off_rect = QtCore.QRect(actions_left + button_width + self._spacing, top_offset, button_width, button_height)
            self._draw_button(
                painter,
                off_rect,
                tr("quick_block_off", "OFF"),
                role="off",
                enabled=True,
                hovered=hover,
                selected=selected,
                palette=palette,
            )

        self._cache_hit_areas(index, on_rect, off_rect)

        painter.setBrush(QtCore.Qt.NoBrush)
        pen = QtGui.QPen(border_color, 1.4)
        painter.setPen(pen)
        painter.drawRoundedRect(container_rect, corner_radius, corner_radius)

        painter.restore()

    def _draw_button(
        self,
        painter: QtGui.QPainter,
        rect: QtCore.QRect,
        text: str,
        *,
        role: str,
        enabled: bool,
        hovered: bool,
        selected: bool,
        palette: QtGui.QPalette,
    ) -> None:
        widget = self._button_templates["on" if role == "on" else "off"]
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(widget)
        option.rect = rect
        option.text = text
        option.state = QtWidgets.QStyle.State_Enabled if enabled else QtWidgets.QStyle.State_None
        if hovered:
            option.state |= QtWidgets.QStyle.State_MouseOver
        button_palette = widget.palette()
        if selected:
            highlight = palette.color(QtGui.QPalette.Highlight).lighter(140)
            text_color = palette.color(QtGui.QPalette.HighlightedText)
            button_palette.setColor(QtGui.QPalette.Button, highlight)
            button_palette.setColor(QtGui.QPalette.ButtonText, text_color)
        option.palette = button_palette
        widget.style().drawControl(QtWidgets.QStyle.CE_PushButton, option, painter, widget)

    def _create_button_widget(self, role: str) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton()
        button.setProperty("semanticRole", role)
        button.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        button.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        button.hide()
        return button

    def _cache_hit_areas(self, index: QtCore.QModelIndex, on_rect: QtCore.QRect, off_rect: QtCore.QRect | None) -> None:
        self._hit_areas[index.row()] = {
            "on": on_rect,
            "off": off_rect or QtCore.QRect(),
        }

    def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> bool:  # type: ignore[override]
        if event.type() == QtCore.QEvent.MouseButtonRelease and index.row() in self._hit_areas:
            item = index.data(QuickBlocksListModel.DATA_ROLE)
            if not item or not item.block:
                return False
            hit = self._hit_areas.get(index.row(), {})
            mouse_event = QtGui.QMouseEvent(event)
            pos = mouse_event.position().toPoint()
            if hit.get("on") and hit["on"].contains(pos):
                self._trigger_callback(item.block.id, "on")
                return True
            if hit.get("off") and hit["off"].contains(pos):
                self._trigger_callback(item.block.id, "off")
                return True
        return super().editorEvent(event, model, option, index)
