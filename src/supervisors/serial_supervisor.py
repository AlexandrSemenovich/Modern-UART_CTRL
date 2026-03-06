"""SerialWorker supervisor with watchdog restart logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

import logging
import time

from PySide6 import QtCore

from src.models.serial_worker import SerialWorker


logger = logging.getLogger(__name__)


WorkerHook = Callable[..., None]


@dataclass(slots=True)
class WorkerSpec:
    port_name: str
    baud_rate: int
    config: dict[str, Any]


@dataclass(slots=True)
class WorkerCallbacks:
    on_rx: WorkerHook
    on_error: WorkerHook
    on_status: WorkerHook
    on_finished: Callable[[], None]


@dataclass(slots=True)
class WorkerContext:
    worker: SerialWorker
    spec: WorkerSpec
    callbacks: WorkerCallbacks
    last_heartbeat: float
    stopping: bool = False
    awaiting_first_heartbeat: bool = True
    fatal_stop: bool = False


class SerialWorkerSupervisor(QtCore.QObject):
    """Supervisor responsible for spawning/stopping SerialWorker threads."""

    def __init__(
        self,
        port_label: str,
        ipc_ports: Iterable[str] | None = None,
        *,
        parent: QtCore.QObject | None = None,
        heartbeat_timeout: float = 1.5,
        watchdog_interval_ms: int = 300,
    ) -> None:
        super().__init__(parent)
        self._port_label = port_label
        self._ipc_ports = list(ipc_ports or [])
        self._contexts: dict[str, WorkerContext] = {}
        self._heartbeat_timeout = heartbeat_timeout

        self._watchdog = QtCore.QTimer(self)
        self._watchdog.setInterval(watchdog_interval_ms)
        self._watchdog.timeout.connect(self._check_workers)
        self._watchdog.start()

    def spawn_worker(
        self,
        *,
        port_name: str,
        baud_rate: int,
        on_rx: WorkerHook,
        on_error: WorkerHook,
        on_status: WorkerHook,
        on_finished: Callable[[], None],
        config: dict[str, Any] | None = None,
    ) -> SerialWorker:
        spec = WorkerSpec(port_name=port_name, baud_rate=baud_rate, config=config or {})
        callbacks = WorkerCallbacks(on_rx, on_error, on_status, on_finished)
        return self._start_worker(spec, callbacks)

    def stop_worker(self, port_label: str) -> None:
        context = self._contexts.get(port_label)
        if not context:
            return
        context.stopping = True
        self._stop_thread(context.worker)

    def _start_worker(self, spec: WorkerSpec, callbacks: WorkerCallbacks) -> SerialWorker:
        port_label = self._port_label
        context = self._contexts.get(port_label)
        if context:
            self.stop_worker(port_label)

        worker = SerialWorker(port_label, spec.config)
        worker.configure(spec.port_name, spec.baud_rate)
        worker.rx.connect(callbacks.on_rx)
        worker.error.connect(callbacks.on_error)
        worker.status.connect(callbacks.on_status)
        worker.heartbeat.connect(self._handle_heartbeat)
        worker.finished.connect(lambda: self._handle_finished(port_label))
        worker.start()

        ctx = WorkerContext(
            worker=worker,
            spec=spec,
            callbacks=callbacks,
            last_heartbeat=time.monotonic(),
            stopping=False,
        )
        self._contexts[port_label] = ctx
        return worker

    def _stop_thread(self, worker: SerialWorker) -> None:
        try:
            worker.stop()
            if worker.isRunning():
                worker.wait(1000)
        except RuntimeError:
            pass

    def _handle_heartbeat(self, port_label: str, timestamp: float) -> None:
        context = self._contexts.get(port_label)
        if context:
            context.last_heartbeat = timestamp
            context.awaiting_first_heartbeat = False

    def _handle_finished(self, port_label: str) -> None:
        context = self._contexts.get(port_label)
        if not context:
            return

        ctx = context
        if ctx.stopping:
            ctx.callbacks.on_finished()
            self._contexts.pop(port_label, None)
            return

        if ctx.worker.fatal_error:
            ctx.callbacks.on_finished()
            self._contexts.pop(port_label, None)
            return

        if not ctx.worker.isRunning():
            ctx.callbacks.on_finished()
            self._contexts.pop(port_label, None)
            return

        # Unexpected termination — notify and restart
        logger.warning("SerialWorker for %s stopped unexpectedly; restarting", port_label)
        ctx.callbacks.on_error(port_label, "Worker crashed; restarting")
        self._restart_worker(port_label)

    def _restart_worker(self, port_label: str) -> None:
        context = self._contexts.get(port_label)
        if not context:
            return
        context.stopping = False
        self._stop_thread(context.worker)
        self._start_worker(context.spec, context.callbacks)

    def _check_workers(self) -> None:
        now = time.monotonic()
        for port_label, context in list(self._contexts.items()):
            if context.stopping:
                continue
            if context.awaiting_first_heartbeat and now - context.last_heartbeat <= self._heartbeat_timeout:
                continue
            if now - context.last_heartbeat > self._heartbeat_timeout:
                logger.warning("Watchdog timeout for %s; restarting worker", port_label)
                context.callbacks.on_status(port_label, "Watchdog restart")
                self._restart_worker(port_label)

