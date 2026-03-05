"""Stopwatch service and state container for UI integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import time

from PySide6 import QtCore

from src.utils.service_container import service_container


@dataclass(frozen=True)
class StopwatchState:
    """Immutable snapshot of the stopwatch state."""

    running: bool
    elapsed_ms: int
    auto_mode: Optional[str] = None


class StopwatchService(QtCore.QObject):
    """High precision stopwatch backed by Qt timer for UI thread."""

    time_changed = QtCore.Signal(str, StopwatchState)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(50)  # ~20 FPS обновление
        self._timer.timeout.connect(self._tick)
        self._start_ts: float | None = None
        self._elapsed_before_pause = 0.0
        self._formatter: Callable[[int], str] = format_duration
        self._state = StopwatchState(running=False, elapsed_ms=0)

    @property
    def state(self) -> StopwatchState:
        return self._state

    def start(self) -> None:
        if self._state.running:
            return
        self._start_ts = time.perf_counter()
        self._timer.start()
        self._update_state(running=True)

    def stop(self) -> None:
        if not self._state.running:
            return
        self._timer.stop()
        self._elapsed_before_pause = self._current_elapsed()
        self._start_ts = None
        self._update_state(running=False)

    def reset(self) -> None:
        self._timer.stop()
        self._start_ts = None
        self._elapsed_before_pause = 0.0
        self._update_state(running=False, elapsed_override=0)

    def set_auto_mode(self, mode: Optional[str]) -> None:
        self._state = StopwatchState(
            running=self._state.running,
            elapsed_ms=self._state.elapsed_ms,
            auto_mode=mode,
        )

    def _tick(self) -> None:
        elapsed_ms = self._current_elapsed()
        self._update_state(elapsed_override=int(elapsed_ms))

    def _current_elapsed(self) -> float:
        if self._start_ts is None:
            return self._elapsed_before_pause
        return (time.perf_counter() - self._start_ts) * 1000 + self._elapsed_before_pause

    def _update_state(self, *, running: Optional[bool] = None, elapsed_override: Optional[int] = None) -> None:
        elapsed = elapsed_override if elapsed_override is not None else int(self._current_elapsed())
        new_state = StopwatchState(
            running=self._state.running if running is None else running,
            elapsed_ms=elapsed,
            auto_mode=self._state.auto_mode,
        )
        self._state = new_state
        self.time_changed.emit(self._formatter(elapsed), new_state)


def format_duration(total_ms: int) -> str:
    """Format milliseconds to dd hh:mm:ss.mmm"""

    if total_ms < 0:
        total_ms = 0
    millis = total_ms % 1000
    total_seconds = total_ms // 1000
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = (total_seconds // 3600) % 24
    days = total_seconds // 86400
    return f"{days:02d} {hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def get_stopwatch_service() -> StopwatchService:
    """Resolve shared stopwatch service from service container."""

    return service_container.resolve("stopwatch_service")


# Register singleton in service container for global reuse
service_container.register_singleton(
    "stopwatch_service",
    lambda: StopwatchService(),
)


__all__ = [
    "StopwatchService",
    "StopwatchState",
    "format_duration",
    "get_stopwatch_service",
]
