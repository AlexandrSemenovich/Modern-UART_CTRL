"""ViewModel для отображения и управления секундомером."""

from __future__ import annotations

from typing import Optional

from PySide6 import QtCore

from src.utils import get_stopwatch_service
from src.utils.stopwatch import StopwatchService, StopwatchState


class StopwatchViewModel(QtCore.QObject):
    """MVVM ViewModel, транслирующий события сервиса секундомера в UI."""

    time_changed = QtCore.Signal(str)
    state_changed = QtCore.Signal(StopwatchState)

    def __init__(
        self,
        parent: QtCore.QObject | None = None,
        *,
        service: StopwatchService | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service or get_stopwatch_service()
        self._formatted_time = self._format_elapsed(self._service.state.elapsed_ms)
        self._state = self._service.state
        self._service.time_changed.connect(self._on_service_time_changed)

    @property
    def formatted_time(self) -> str:
        return self._formatted_time

    @property
    def state(self) -> StopwatchState:
        return self._state

    def start_manual(self) -> None:
        self._service.start()

    def stop_manual(self) -> None:
        self._service.stop()

    def reset_manual(self) -> None:
        self._service.reset()

    def toggle_manual(self) -> None:
        if self._state.running:
            self.stop_manual()
        else:
            self.start_manual()

    def set_auto_mode(self, mode: Optional[str]) -> None:
        self._service.set_auto_mode(mode)

    def _on_service_time_changed(self, formatted: str, state: StopwatchState) -> None:
        self._formatted_time = formatted
        self._state = state
        self.time_changed.emit(formatted)
        self.state_changed.emit(state)

    @staticmethod
    def _format_elapsed(elapsed_ms: int) -> str:
        from src.utils.stopwatch import format_duration

        return format_duration(elapsed_ms)


__all__ = ["StopwatchViewModel"]
