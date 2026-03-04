"""Reusable skeleton-loading widgets with shimmer animation."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class ShimmerPlaceholder(QtWidgets.QFrame):
    """Rectangular placeholder with animated shimmer effect."""

    def __init__(self, width: int | None = None, height: int | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("shimmer_placeholder")
        self.setMinimumHeight(height or 28)
        if width:
            self.setMinimumWidth(width)
            self.setMaximumWidth(width)

        # Gradient for shimmering highlight
        self._gradient_position = 0.0
        self._animation = QtCore.QPropertyAnimation(self, b"gradientPosition", self)
        self._animation.setDuration(1200)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setLoopCount(-1)
        self._animation.start()

    def sizeHint(self) -> QtCore.QSize:  # type: ignore[override]
        hint = super().sizeHint()
        if hint.height() <= 0:
            hint.setHeight(28)
        return hint

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # type: ignore[override]
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = self.rect()
        radius = min(10, rect.height() // 2)

        palette = self.palette()
        base_color = palette.color(QtGui.QPalette.AlternateBase)
        highlight_color = palette.color(QtGui.QPalette.Highlight)

        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.topRight())
        # Create shimmer band using gradient position
        band_start = max(0.0, self._gradient_position - 0.2)
        band_end = min(1.0, self._gradient_position + 0.2)
        gradient.setColorAt(0.0, base_color)
        gradient.setColorAt(band_start, base_color)
        gradient.setColorAt(self._gradient_position, highlight_color.lighter(160))
        gradient.setColorAt(band_end, base_color)
        gradient.setColorAt(1.0, base_color)

        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)

    def getGradientPosition(self) -> float:
        return self._gradient_position

    def setGradientPosition(self, value: float) -> None:
        self._gradient_position = value
        self.update()

    gradientPosition = QtCore.Property(float, getGradientPosition, setGradientPosition)  # type: ignore[var-annotated]


class SkeletonPanelPlaceholder(QtWidgets.QFrame):
    """Stacked skeleton layout used inside panels."""

    def __init__(self, row_count: int = 3, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("skeleton_panel_placeholder")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for index in range(row_count):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(8)

            # Leading circle (icon substitute)
            bubble = ShimmerPlaceholder(32, 32)
            bubble.setObjectName("skeleton_circle")
            row.addWidget(bubble, 0)

            # Two stacked lines
            column = QtWidgets.QVBoxLayout()
            column.setSpacing(6)

            line_full = ShimmerPlaceholder()
            line_full.setMinimumHeight(18)
            column.addWidget(line_full)

            line_short = ShimmerPlaceholder()
            line_short.setMinimumHeight(14)
            line_short.setMaximumWidth(180 if index % 2 else 240)
            column.addWidget(line_short)

            row.addLayout(column, 1)

            layout.addLayout(row)

        layout.addStretch(1)
