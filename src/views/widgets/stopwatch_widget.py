"""Виджет секундомера, синхронизированный с StopwatchViewModel."""

from __future__ import annotations

from PySide6 import QtWidgets, QtCore, QtGui

from src.styles.constants import Fonts, Sizes
from src.utils.translator import tr, translator
from src.viewmodels.stopwatch_viewmodel import StopwatchViewModel


class StopwatchWidget(QtWidgets.QWidget):
    """Компактный виджет секундомера с управлением."""

    def __init__(
        self,
        viewmodel: StopwatchViewModel,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._viewmodel = viewmodel
        self.setObjectName("stopwatch_widget")
        self._build_ui()
        self._bind_viewmodel()
        translator.language_changed.connect(self._retranslate_ui)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QtWidgets.QFrame()
        card.setObjectName("stopwatch_card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(
            Sizes.CARD_MARGIN,
            Sizes.CARD_MARGIN,
            Sizes.CARD_MARGIN,
            Sizes.CARD_MARGIN,
        )

        self._lbl_display = QtWidgets.QLabel("00 00:00:00.000")
        display_font = QtGui.QFont("OCR A Extended", 32)
        display_font.setStyleHint(QtGui.QFont.Monospace)
        display_font.setFixedPitch(True)
        self._lbl_display.setFont(display_font)
        self._lbl_display.setAlignment(QtCore.Qt.AlignCenter)
        self._lbl_display.setObjectName("stopwatch_display")
        card_layout.addWidget(self._lbl_display)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(Sizes.LAYOUT_SPACING)

        self._btn_start = QtWidgets.QPushButton()
        self._btn_stop = QtWidgets.QPushButton()
        self._btn_reset = QtWidgets.QPushButton()
        self._retranslate_ui()

        buttons_layout.addWidget(self._btn_start)
        buttons_layout.addWidget(self._btn_stop)
        buttons_layout.addWidget(self._btn_reset)

        card_layout.addLayout(buttons_layout)
        layout.addWidget(card)

    def _bind_viewmodel(self) -> None:
        self._btn_start.clicked.connect(self._viewmodel.start_manual)
        self._btn_stop.clicked.connect(self._viewmodel.stop_manual)
        self._btn_reset.clicked.connect(self._viewmodel.reset_manual)
        self._viewmodel.time_changed.connect(self._update_display)
        self._viewmodel.state_changed.connect(self._update_state)
        self._update_display(self._viewmodel.formatted_time)
        self._update_state(self._viewmodel.state)

    def _update_display(self, formatted: str) -> None:
        self._lbl_display.setText(formatted)

    def _update_state(self, state) -> None:
        self._btn_start.setEnabled(not state.running)
        self._btn_stop.setEnabled(state.running)
        self._btn_reset.setEnabled(True)

    def _retranslate_ui(self) -> None:
        self._btn_start.setText(tr("stopwatch_start", "Start"))
        self._btn_stop.setText(tr("stopwatch_stop", "Stop"))
        self._btn_reset.setText(tr("stopwatch_reset", "Reset"))


__all__ = ["StopwatchWidget"]
