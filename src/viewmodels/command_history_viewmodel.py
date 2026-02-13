"""Command history persistence and table models."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Iterable
import json
import datetime
import configparser

from PySide6 import QtCore


@dataclass
class CommandHistoryEntry:
    """Represents a single record inside the command history."""

    command: str
    port: str
    status: str
    timestamp: str

    def to_display_tuple(self) -> tuple[str, str, str, str]:
        return (self.command, self.port, self.status, self.timestamp)


class CommandHistoryModel(QtCore.QObject):
    """Stores command history entries with disk persistence."""

    entries_changed = QtCore.Signal()

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: List[CommandHistoryEntry] = []
        self._storage_path = self._resolve_storage_path()
        self._max_items = self._load_max_items()
        self.load()

    @staticmethod
    def _resolve_storage_path() -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "config" / "command_history.json"

    def _load_max_items(self) -> int:
        config_path = Path(__file__).resolve().parents[2] / "config" / "config.ini"
        parser = configparser.ConfigParser()
        try:
            parser.read(config_path, encoding="utf-8")
            return parser.getint("ui", "max_history_items", fallback=200)
        except Exception:
            return 200

    def load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as handle:
                raw_items = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        self._entries = [
            CommandHistoryEntry(
                command=item.get("command", ""),
                port=item.get("port", "unknown"),
                status=item.get("status", "unknown"),
                timestamp=item.get("timestamp", ""),
            )
            for item in raw_items
            if item.get("command")
        ][: self._max_items]
        self.entries_changed.emit()

    def save(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(entry) for entry in self._entries[: self._max_items]]
        try:
            with self._storage_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def entries(self) -> List[CommandHistoryEntry]:
        return list(self._entries)

    def entry_count(self) -> int:
        return len(self._entries)

    def add_entry(self, command: str, port: str, status: str = "success") -> None:
        command = command.strip()
        if not command:
            return
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        entry = CommandHistoryEntry(command=command, port=port, status=status, timestamp=timestamp)
        self._entries.insert(0, entry)
        self._entries = self._entries[: self._max_items]
        self.entries_changed.emit()
        self.save()

    def remove_indices(self, indices: Iterable[int]) -> None:
        sorted_indices = sorted(set(idx for idx in indices if 0 <= idx < len(self._entries)), reverse=True)
        if not sorted_indices:
            return
        for idx in sorted_indices:
            self._entries.pop(idx)
        self.entries_changed.emit()
        self.save()

    def clear(self) -> None:
        if not self._entries:
            return
        self._entries.clear()
        self.entries_changed.emit()
        self.save()

    def export_to_file(self, path: Path) -> bool:
        try:
            with path.open("w", encoding="utf-8") as handle:
                for entry in self._entries:
                    handle.write("\t".join(entry.to_display_tuple()) + "\n")
            return True
        except OSError:
            return False


class CommandHistoryTableModel(QtCore.QAbstractTableModel):
    """Qt model for binding command history to QTableView."""

    HEADERS = ("command", "port", "status", "timestamp")

    def __init__(self, model: CommandHistoryModel, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._model = model
        model.entries_changed.connect(self._on_entries_changed)

    def _on_entries_changed(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    # Qt overrides
    def rowCount(self, parent: QtCore.QModelIndex | None = None) -> int:  # type: ignore[override]
        return 0 if parent and parent.isValid() else self._model.entry_count()

    def columnCount(self, parent: QtCore.QModelIndex | None = None) -> int:  # type: ignore[override]
        return 0 if parent and parent.isValid() else len(self.HEADERS)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        entry = self._model.entries()[index.row()]
        column_map = {
            0: entry.command,
            1: entry.port,
            2: entry.status,
            3: entry.timestamp,
        }
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return column_map.get(index.column())
        if role == QtCore.Qt.UserRole:
            return entry
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return super().headerData(section, orientation, role)
        if 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def entry_at(self, row: int) -> CommandHistoryEntry | None:
        entries = self._model.entries()
        if 0 <= row < len(entries):
            return entries[row]
        return None
