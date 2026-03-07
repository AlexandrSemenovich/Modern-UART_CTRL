"""Widget Host module adapters for built-in modules."""

from __future__ import annotations

from typing import Any, Callable

from PySide6 import QtCore, QtWidgets

from src.utils import (
    get_quick_blocks_repository,
    get_widget_host_viewmodel,
)
from src.utils.service_container import service_container
from src.viewmodels.widget_module_descriptor import WidgetModuleDescriptor


class WidgetHostModuleAdapter:
    """Base adapter that converts DSL entry to WidgetModuleDescriptor."""

    def __init__(self, entry: dict[str, Any]) -> None:
        self._entry = entry

    def build(self) -> WidgetModuleDescriptor:
        raise NotImplementedError


class StopwatchHostAdapter(WidgetHostModuleAdapter):
    """Adapter wiring StopwatchWidget with shared ViewModel factory."""

    def build(self) -> WidgetModuleDescriptor:
        from src.views.widgets.stopwatch_widget import StopwatchWidget

        module_id = self._entry["id"]
        title = self._entry.get("title", "Stopwatch")
        icon = self._entry.get("icon")
        layout_hint = self._entry.get("layout_hint")

        def viewmodel_factory() -> QtCore.QObject | None:
            factory = service_container.resolve("viewmodel_factory")
            return factory.create_stopwatch_viewmodel()

        def view_factory(
            parent: QtWidgets.QWidget | None, viewmodel: QtCore.QObject | None
        ) -> QtWidgets.QWidget:
            vm = viewmodel or viewmodel_factory()
            return StopwatchWidget(vm, parent)

        return WidgetModuleDescriptor(
            module_id=module_id,
            title=title,
            view_factory=view_factory,
            viewmodel_factory=viewmodel_factory,
            icon_name=icon,
            layout_hint=layout_hint,
        )


class LogsHostAdapter(WidgetHostModuleAdapter):
    """Adapter embedding ConsolePanelView inside Widget Host."""

    def build(self) -> WidgetModuleDescriptor:
        from src.views.console_panel_view import ConsolePanelView

        module_id = self._entry["id"]
        title = self._entry.get("title", "Logs")
        icon = self._entry.get("icon")
        layout_hint = self._entry.get("layout_hint")

        def view_factory(
            parent: QtWidgets.QWidget | None, viewmodel: QtCore.QObject | None
        ) -> QtWidgets.QWidget:
            return ConsolePanelView(parent=parent)

        return WidgetModuleDescriptor(
            module_id=module_id,
            title=title,
            view_factory=view_factory,
            viewmodel_factory=None,
            icon_name=icon,
            layout_hint=layout_hint,
        )


class QuickCommandsHostAdapter(WidgetHostModuleAdapter):
    """Adapter wiring QuickBlocksPanel to shared repository."""

    def build(self) -> WidgetModuleDescriptor:
        from src.views.quick_blocks_panel import QuickBlocksPanel

        module_id = self._entry["id"]
        title = self._entry.get("title", "Quick Commands")
        icon = self._entry.get("icon")
        layout_hint = self._entry.get("layout_hint")
        repository = get_quick_blocks_repository()

        def view_factory(
            parent: QtWidgets.QWidget | None, viewmodel: QtCore.QObject | None
        ) -> QtWidgets.QWidget:
            panel = QuickBlocksPanel(repository, parent)
            return panel

        return WidgetModuleDescriptor(
            module_id=module_id,
            title=title,
            view_factory=view_factory,
            viewmodel_factory=None,
            icon_name=icon,
            layout_hint=layout_hint,
        )


MODULE_ADAPTERS: dict[str, type[WidgetHostModuleAdapter]] = {
    "stopwatch": StopwatchHostAdapter,
    "logs": LogsHostAdapter,
    "quick_commands": QuickCommandsHostAdapter,
}


__all__ = [
    "WidgetHostModuleAdapter",
    "StopwatchHostAdapter",
    "LogsHostAdapter",
    "QuickCommandsHostAdapter",
    "MODULE_ADAPTERS",
]
