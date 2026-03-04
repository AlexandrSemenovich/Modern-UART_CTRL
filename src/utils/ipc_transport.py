"""Cross-process transport utilities for SerialWorker supervision.

This module introduces a simple IPC layer built on top of
``multiprocessing.Queue`` and ``multiprocessing.shared_memory`` so that the
GUI process can exchange commands/events with worker processes without
reinventing serialization for every consumer.

Key building blocks:

``IPCCommandQueue`` / ``IPCEventQueue``
    Lightweight wrappers above ``multiprocessing.Queue`` that automatically
    stamp outgoing messages with UUID/timestamps and expose typed helpers to
    compose/parse payloads.

``SharedBuffer`` / ``SharedBufferPool``
    Shared-memory ring buffers (512 KB per port) that store binary RX/TX
    chunks referenced from queue messages. Each chunk descriptor contains
    the shared memory name, byte offset, payload length and CRC32 checksum
    so integrity can be validated by the receiver.

``IPCTransport``
    High-level façade bundling command/event queues and shared buffers. The
    GUI side can vend the transport to worker processes via ``spawn`` or
    ``forkserver`` without leaking PySide6/QObjects into the child process.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from multiprocessing import Queue, Lock, Value
from multiprocessing.shared_memory import SharedMemory
from typing import Any, Iterable, TypedDict

import json
import time
import uuid
import zlib


DEFAULT_BUFFER_SIZE = 512 * 1024  # 512 KB per port


class SharedChunk(TypedDict):
    """Descriptor that identifies a payload inside a shared buffer."""

    buffer_name: str
    offset: int
    length: int
    crc32: int


@dataclass(slots=True)
class IPCHeader:
    """Metadata attached to every IPC command/event."""

    message_id: str
    port: str
    kind: str
    timestamp: float


@dataclass(slots=True)
class IPCMessage:
    """Envelope describing commands/events travelling across the queues."""

    header: IPCHeader
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "header": asdict(self.header),
            "payload": self.payload,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "IPCMessage":
        header_dict = data.get("header", {})
        header = IPCHeader(
            message_id=header_dict.get("message_id", ""),
            port=header_dict.get("port", ""),
            kind=header_dict.get("kind", "unknown"),
            timestamp=float(header_dict.get("timestamp", time.time())),
        )
        payload = data.get("payload", {})
        return IPCMessage(header=header, payload=payload)


class IPCQueue:
    """Thin wrapper around ``multiprocessing.Queue`` with typed helpers."""

    def __init__(self, queue: Queue | None = None) -> None:
        self._queue: Queue = queue or Queue()

    @property
    def raw(self) -> Queue:
        return self._queue

    def send(self, port: str, kind: str, payload: dict[str, Any]) -> str:
        message_id = uuid.uuid4().hex
        header = IPCHeader(
            message_id=message_id,
            port=port,
            kind=kind,
            timestamp=time.time(),
        )
        self._queue.put(IPCMessage(header, payload).to_dict())
        return message_id

    def put(self, message: IPCMessage) -> None:
        self._queue.put(message.to_dict())

    def get(self, timeout: float | None = None) -> IPCMessage:
        data = self._queue.get(timeout=timeout)
        if isinstance(data, (bytes, str)):
            data = json.loads(data)
        return IPCMessage.from_dict(data)

    def empty(self) -> bool:
        return self._queue.empty()


class SharedBuffer:
    """Lock-protected shared-memory ring buffer."""

    def __init__(self, *, size: int = DEFAULT_BUFFER_SIZE, name: str | None = None) -> None:
        self._size = size
        self._shm = SharedMemory(name=name, create=True, size=size)
        self._lock = Lock()
        self._write_offset = Value("I", 0)

    @property
    def name(self) -> str:
        return self._shm.name

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        self._shm.unlink()

    def write(self, data: bytes) -> SharedChunk:
        if not data:
            raise ValueError("Chunk data must be non-empty")
        if len(data) > self._size:
            raise ValueError("Chunk size exceeds shared buffer capacity")

        with self._lock:
            offset = self._write_offset.value
            if offset + len(data) > self._size:
                offset = 0
                self._write_offset.value = 0

            self._shm.buf[offset : offset + len(data)] = data
            self._write_offset.value = offset + len(data)

        checksum = zlib.crc32(data) & 0xFFFFFFFF
        return SharedChunk(
            buffer_name=self._shm.name,
            offset=offset,
            length=len(data),
            crc32=checksum,
        )

    def read(self, descriptor: SharedChunk) -> bytes:
        offset = descriptor["offset"]
        length = descriptor["length"]
        if offset + length > self._size:
            raise ValueError("Descriptor exceeds buffer bounds")
        payload = bytes(self._shm.buf[offset : offset + length])
        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        if checksum != descriptor["crc32"]:
            raise ValueError("CRC mismatch for shared chunk")
        return payload


class SharedBufferPool:
    """Manages per-port shared buffers."""

    def __init__(self, ports: Iterable[str], *, size: int = DEFAULT_BUFFER_SIZE) -> None:
        self._buffers: dict[str, SharedBuffer] = {}
        for port in ports:
            self._buffers[port] = SharedBuffer(size=size)

    def buffer_for(self, port: str) -> SharedBuffer:
        if port not in self._buffers:
            self._buffers[port] = SharedBuffer()
        return self._buffers[port]

    def write_chunk(self, port: str, data: bytes) -> SharedChunk:
        return self.buffer_for(port).write(data)

    def read_chunk(self, port: str, descriptor: SharedChunk) -> bytes:
        return self.buffer_for(port).read(descriptor)

    def close_all(self) -> None:
        for buffer in self._buffers.values():
            buffer.close()

    def unlink_all(self) -> None:
        for buffer in self._buffers.values():
            try:
                buffer.unlink()
            except FileNotFoundError:
                pass


class IPCTransport:
    """Bundles command/event queues with shared-memory buffers."""

    def __init__(self, ports: Iterable[str]) -> None:
        self.commands = IPCQueue()
        self.events = IPCQueue()
        self.buffers = SharedBufferPool(ports)

    def send_command(self, port: str, kind: str, payload: dict[str, Any]) -> str:
        return self.commands.send(port, kind, payload)

    def send_event(self, port: str, kind: str, payload: dict[str, Any]) -> str:
        return self.events.send(port, kind, payload)

    def publish_chunk(self, port: str, data: bytes) -> SharedChunk:
        return self.buffers.write_chunk(port, data)

    def fetch_chunk(self, port: str, descriptor: SharedChunk) -> bytes:
        return self.buffers.read_chunk(port, descriptor)

    def shutdown(self) -> None:
        self.buffers.close_all()

