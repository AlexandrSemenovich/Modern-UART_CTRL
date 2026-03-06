from __future__ import annotations

import time

import pytest
from PySide6 import QtCore

import src.supervisors.serial_supervisor as supervisor_module


class DummyWorker(QtCore.QObject):
    """Lightweight stand-in for SerialWorker used in unit tests."""

    rx = QtCore.Signal(str, str)
    error = QtCore.Signal(str, str)
    status = QtCore.Signal(str, str)
    heartbeat = QtCore.Signal(str, float)
    finished = QtCore.Signal()

    start_count = 0
    stop_count = 0
    instances: list["DummyWorker"] = []

    def __init__(self, port_label: str, config: dict | None = None) -> None:
        super().__init__()
        self._port_label = port_label
        self._config = config or {}
        self._running = False
        self._port_name: str | None = None
        self._baud_rate: int | None = None
        self.fatal_error = False
        DummyWorker.instances.append(self)

    @classmethod
    def reset(cls) -> None:
        cls.start_count = 0
        cls.stop_count = 0
        cls.instances.clear()

    def configure(self, port_name: str, baud_rate: int) -> None:
        self._port_name = port_name
        self._baud_rate = baud_rate

    def start(self) -> None:
        self._running = True
        DummyWorker.start_count += 1

    def stop(self) -> None:
        self._running = False
        DummyWorker.stop_count += 1

    def isRunning(self) -> bool:  # noqa: N802 - Qt style
        return self._running

    def wait(self, _: int) -> None:
        return None

    def emit_heartbeat(self, timestamp: float | None = None) -> None:
        self.heartbeat.emit(self._port_label, timestamp or time.monotonic())


@pytest.fixture
def supervisor(monkeypatch, qapp):  # noqa: PT004 - needs qapp fixture
    DummyWorker.reset()
    monkeypatch.setattr(supervisor_module, "SerialWorker", DummyWorker)
    sup = supervisor_module.SerialWorkerSupervisor(
        "CPU1",
        heartbeat_timeout=0.05,
        watchdog_interval_ms=5,
    )
    sup._watchdog.stop()
    yield sup
    sup.deleteLater()


def _spawn(supervisor, **callbacks):
    defaults = {
        "on_rx": lambda *args: None,
        "on_error": lambda *args: None,
        "on_status": lambda *args: None,
        "on_finished": lambda: None,
    }
    defaults.update(callbacks)
    supervisor.spawn_worker(
        port_name="COM1",
        baud_rate=115200,
        on_rx=defaults["on_rx"],
        on_error=defaults["on_error"],
        on_status=defaults["on_status"],
        on_finished=defaults["on_finished"],
    )


def test_unexpected_finish_triggers_restart(supervisor):
    errors: list[tuple[str, str]] = []

    _spawn(supervisor, on_error=lambda *args: errors.append(args))
    assert DummyWorker.start_count == 1

    supervisor._handle_finished("CPU1")

    assert DummyWorker.start_count == 2, "Supervisor should respawn worker"
    assert errors[-1] == ("CPU1", "Worker crashed; restarting")


def test_watchdog_restart_on_missed_heartbeat(supervisor):
    statuses: list[tuple[str, str]] = []

    _spawn(supervisor, on_status=lambda *args: statuses.append(args))
    ctx = supervisor._contexts["CPU1"]
    ctx.last_heartbeat = time.monotonic() - 10

    supervisor._check_workers()

    assert statuses[-1] == ("CPU1", "Watchdog restart")
    assert DummyWorker.start_count == 2


def test_stop_worker_marks_context_and_cleans_on_finish(supervisor):
    finished_calls: list[bool] = []

    _spawn(supervisor, on_finished=lambda: finished_calls.append(True))

    supervisor.stop_worker("CPU1")
    ctx = supervisor._contexts["CPU1"]
    assert ctx.stopping is True

    supervisor._handle_finished("CPU1")

    assert finished_calls == [True]
    assert "CPU1" not in supervisor._contexts
