"""Отдельное окно-виджет секундомера."""

from __future__ import annotations

from PySide6 import QtWidgets, QtCore, QtGui

from src.viewmodels.stopwatch_viewmodel import StopwatchViewModel
from src.views.widgets.stopwatch_widget import StopwatchWidget
from src.utils.translator import tr


class StopwatchWindow(QtWidgets.QWidget):
    """Отдельное окно с секундомером, открываемое из меню."""

    def __init__(
        self,
        viewmodel: StopwatchViewModel,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent, QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        self.setWindowTitle(tr("stopwatch_window_title", "Stopwatch"))
        self._viewmodel = viewmodel
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        card = QtWidgets.QFrame()
        card.setObjectName("stopwatch_window_card")
        card.setFrameShape(QtWidgets.QFrame.StyledPanel)
        card.setFrameShadow(QtWidgets.QFrame.Plain)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self._widget = StopwatchWidget(viewmodel)
        card_layout.addWidget(self._widget)
        layout.addWidget(card)

        self.resize(340, 220)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        event.ignore()
        self.hide()


__all__ = ["StopwatchWindow"]
