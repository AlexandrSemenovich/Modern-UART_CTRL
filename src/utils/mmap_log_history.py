"""Memory-mapped log history storage."""

from __future__ import annotations

import mmap
import os
import struct
from pathlib import Path

from src.utils.paths import get_config_dir


class MemoryMappedLogHistory:
    """Fixed-size circular history stored in a memory-mapped file."""

    _HEADER = struct.Struct("<QQ")  # write_offset, total_written

    def __init__(self, port_label: str, capacity_bytes: int) -> None:
        if capacity_bytes <= self._HEADER.size:
            raise ValueError("capacity_bytes must exceed header size")

        safe_label = port_label.lower().replace("/", "_")
        self._path = get_config_dir() / f"console_history_{safe_label}.bin"
        self._total_size = capacity_bytes
        self._payload_size = self._total_size - self._HEADER.size

        self._file = self._open_file()
        self._mmap = mmap.mmap(self._file.fileno(), 0)

        self._write_offset, self._total_written = self._read_header()

    def _open_file(self) -> "os.PathLike[str]":  # type: ignore[override]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists() or self._path.stat().st_size != self._total_size:
            with open(self._path, "wb") as handle:
                handle.truncate(self._total_size)
        return open(self._path, "r+b")

    def _read_header(self) -> tuple[int, int]:
        raw = self._mmap[: self._HEADER.size]
        if len(raw) != self._HEADER.size:
            return 0, 0
        write_offset, total_written = self._HEADER.unpack(raw)
        write_offset = min(write_offset, self._payload_size - 1) if self._payload_size else 0
        return write_offset, total_written

    def _write_header(self) -> None:
        self._HEADER.pack_into(self._mmap, 0, self._write_offset, self._total_written)
        self._mmap.flush()

    def append(self, text: str) -> None:
        if not text:
            return
        payload = text.replace("\r\n", "\n").encode("utf-8")
        if not payload.endswith(b"\n"):
            payload += b"\n"

        if len(payload) >= self._payload_size:
            payload = payload[-self._payload_size :]

        payload_offset = self._HEADER.size
        offset = self._write_offset
        end = offset + len(payload)

        if end <= self._payload_size:
            start = payload_offset + offset
            self._mmap[start : start + len(payload)] = payload
        else:
            first = self._payload_size - offset
            start = payload_offset + offset
            self._mmap[start : start + first] = payload[:first]
            remaining = len(payload) - first
            self._mmap[payload_offset : payload_offset + remaining] = payload[first:]

        self._write_offset = (offset + len(payload)) % self._payload_size
        self._total_written += len(payload)
        self._write_header()

    def read_all(self) -> str:
        if self._payload_size <= 0:
            return ""
        payload_offset = self._HEADER.size
        data_len = min(self._total_written, self._payload_size)
        if data_len <= 0:
            return ""

        if self._total_written < self._payload_size:
            buf = self._mmap[payload_offset : payload_offset + data_len]
            return buf.rstrip(b"\x00").decode("utf-8", errors="ignore")

        offset = self._write_offset
        end = payload_offset + self._payload_size
        tail = self._mmap[payload_offset + offset : end]
        head = self._mmap[payload_offset : payload_offset + offset]
        buf = tail + head
        return buf.decode("utf-8", errors="ignore")

    def close(self) -> None:
        try:
            if hasattr(self, "_mmap"):
                self._mmap.flush()
                self._mmap.close()
        finally:
            if hasattr(self, "_file"):
                self._file.close()


def create_history_for_port(port_label: str, capacity_bytes: int) -> MemoryMappedLogHistory:
    return MemoryMappedLogHistory(port_label, capacity_bytes)
