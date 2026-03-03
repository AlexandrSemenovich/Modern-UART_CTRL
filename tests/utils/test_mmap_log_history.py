"""Tests for memory-mapped log history ring buffer."""

from __future__ import annotations

import os

import pytest

from src.utils.mmap_log_history import MemoryMappedLogHistory


@pytest.fixture(autouse=True)
def _isolate_config_dir(tmp_path, monkeypatch):
    """Redirect config directory to a temporary path for each test."""
    monkeypatch.setenv("UART_CTRL_CONFIG_DIR", str(tmp_path))
    yield


def test_history_appends_and_persists(tmp_path):
    history = MemoryMappedLogHistory("CPU1", 1024)
    history.append("first line")
    history.append("second line")

    data = history.read_all()
    assert "first line" in data
    assert data.rstrip().endswith("second line")

    history.close()

    reopened = MemoryMappedLogHistory("CPU1", 1024)
    try:
        data_after_reopen = reopened.read_all()
        assert "first line" in data_after_reopen
        assert "second line" in data_after_reopen
    finally:
        reopened.close()


def test_history_wraps_and_discards_old_data(tmp_path):
    payload_size = 64
    total_size = payload_size + 16  # header is 16 bytes
    history = MemoryMappedLogHistory("CPU2", total_size)

    for idx in range(12):
        history.append(f"line-{idx}")

    data = history.read_all()
    history.close()

    assert "line-11" in data
    assert "line-10" in data
    assert "line-0" not in data
