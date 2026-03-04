from __future__ import annotations

import time

import pytest
from PySide6 import QtCore

from src.views.console_panel_view import ConsolePanelView


@pytest.fixture
def console_panel(qapp):
    panel = ConsolePanelView(config={
        "batch_interval_ms": 10,
        "max_pending_chunks": 5,
        "back_pressure_threshold": 0.6,
    })
    yield panel
    panel.deleteLater()


def _drain_events(timeout_ms: int = 50):
    end = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < end:
        QtCore.QCoreApplication.processEvents()


def test_back_pressure_drops_when_queue_exceeds(console_panel):
    port = "CPU1"
    for i in range(20):
        console_panel.append_log(port, f"<span>{i}</span><br>", f"{i}\n")
    _drain_events(30)
    dropped = console_panel._dropped_updates.get(port, 0)
    assert dropped > 0
    assert len(console_panel._pending_updates) >= 0


def test_flush_timer_batches_updates(console_panel):
    port = "CPU1"
    console_panel.append_log(port, "<span>A</span><br>", "A\n")
    assert console_panel._update_timer.isActive()
    _drain_events(30)
    assert console_panel._pending_updates == {}
