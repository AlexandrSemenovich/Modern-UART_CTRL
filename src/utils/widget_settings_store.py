"""Хранилище настроек окна Widget Host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json

from PySide6 import QtCore

from src.utils.service_container import service_container


@dataclass
class WidgetHostState:
    """Сериализуемое состояние хоста."""

    geometry: bytes | None = None
    screen_name: str | None = None
    always_on_top: bool = False
    layout_snapshot: dict[str, Any] | None = None


class WidgetSettingsStore:
    """QSettings-основанное хранилище пользовательских настроек."""

    SECTION = "widget_host"

    def __init__(self) -> None:
        self._settings = QtCore.QSettings("UART_CTRL", "WidgetHost")

    def load(self) -> WidgetHostState:
        self._settings.beginGroup(self.SECTION)
        geometry_hex = self._settings.value("geometry", None)
        geometry = bytes.fromhex(geometry_hex) if isinstance(geometry_hex, str) and geometry_hex else None
        state = WidgetHostState(
            geometry=geometry,
            screen_name=self._settings.value("screen_name", type=str),
            always_on_top=bool(self._settings.value("always_on_top", False, type=bool)),
            layout_snapshot=self._read_layout_snapshot(),
        )
        self._settings.endGroup()
        return state

    def save(self, state: WidgetHostState) -> None:
        self._settings.beginGroup(self.SECTION)
        if state.geometry:
            self._settings.setValue("geometry", bytes(state.geometry).hex())
        else:
            self._settings.setValue("geometry", "")
        self._settings.setValue("screen_name", state.screen_name or "")
        self._settings.setValue("always_on_top", state.always_on_top)
        self._settings.setValue("layout_snapshot", json.dumps(state.layout_snapshot or {}, ensure_ascii=False))
        self._settings.endGroup()

    def update_geometry(self, geometry: bytes) -> None:
        state = self.load()
        state.geometry = geometry
        self.save(state)

    def update_screen(self, screen_name: str | None) -> None:
        state = self.load()
        state.screen_name = screen_name
        self.save(state)

    def toggle_on_top(self, enabled: bool) -> None:
        state = self.load()
        state.always_on_top = enabled
        self.save(state)

    def save_layout_snapshot(self, snapshot: dict[str, Any]) -> None:
        state = self.load()
        state.layout_snapshot = snapshot
        self.save(state)

    def _read_layout_snapshot(self) -> dict[str, Any]:
        raw = self._settings.value("layout_snapshot", "")
        if not isinstance(raw, str) or not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}


service_container.register_singleton("widget_settings_store", lambda: WidgetSettingsStore())


__all__ = ["WidgetSettingsStore", "WidgetHostState"]
