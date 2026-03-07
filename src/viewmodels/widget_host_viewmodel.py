"""ViewModel и реестр модулей виджет-хоста."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence, Any

from PySide6 import QtCore, QtWidgets

import yaml

from src.utils.service_container import service_container
from src.viewmodels.widget_module_descriptor import WidgetModuleDescriptor
from src.viewmodels.widget_modules import MODULE_ADAPTERS


class WidgetModuleError(RuntimeError):
    """Исключение, сигнализирующее о проблеме при создании модуля."""


class ModuleDockItem(QtCore.QObject):
    """UI-агностичная сущность карточки, содержащая View и ViewModel."""

    closed = QtCore.Signal()

    def __init__(
        self,
        dock_id: str,
        descriptor: WidgetModuleDescriptor,
        *,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.dock_id = dock_id
        self.descriptor = descriptor
        self.viewmodel = (
            descriptor.viewmodel_factory()
            if descriptor.viewmodel_factory
            else None
        )
        self.view = descriptor.view_factory(None, self.viewmodel)

    def cleanup(self) -> None:
        """Освободить ресурсы view/viewmodel."""

        if hasattr(self.viewmodel, "deleteLater"):
            self.viewmodel.deleteLater()
        if hasattr(self.view, "deleteLater"):
            self.view.deleteLater()
        self.closed.emit()


class WidgetModuleRegistry(QtCore.QObject):
    """Хранилище зарегистрированных дескрипторов модулей."""

    changed = QtCore.Signal()

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__()
        self._modules: dict[str, WidgetModuleDescriptor] = {}
        self._config_path = Path(config_path or "config/widget_modules.yaml")

    def load_from_yaml(self, path: str | None = None) -> None:
        target = Path(path) if path else self._config_path
        with open(target, "r", encoding="utf-8") as fh:
            document = yaml.safe_load(fh) or {}
        modules = document.get("modules", [])
        self._modules.clear()
        for entry in modules:
            descriptor = self._descriptor_from_entry(entry)
            self._modules[descriptor.module_id] = descriptor
        self.changed.emit()

    def _descriptor_from_entry(self, entry: dict) -> WidgetModuleDescriptor:
        module_id = entry.get("id")
        title = entry.get("title", module_id or "Unnamed")

        adapter_key = entry.get("viewmodel_factory") or module_id
        adapter_cls = MODULE_ADAPTERS.get(adapter_key)
        if adapter_cls:
            adapter = adapter_cls(entry)
            return adapter.build()

        def view_factory(
            parent: QtWidgets.QWidget | None, viewmodel: QtCore.QObject | None
        ) -> QtWidgets.QWidget:
            view_class_path = entry.get("view_class")
            if not view_class_path:
                raise WidgetModuleError(f"Module '{module_id}' missing view_class")
            module_name, class_name = view_class_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            if viewmodel is not None:
                try:
                    return cls(viewmodel, parent)
                except TypeError:
                    return cls(parent)
            return cls(parent)

        def viewmodel_factory() -> QtCore.QObject | None:
            factory_alias = entry.get("viewmodel_factory")
            if not factory_alias:
                return None
            factory = service_container.resolve("viewmodel_factory")
            creator = getattr(factory, f"create_{factory_alias}_viewmodel", None)
            if not creator:
                raise WidgetModuleError(
                    f"Factory alias '{factory_alias}' is not supported"
                )
            return creator()

        return WidgetModuleDescriptor(
            module_id=module_id,
            title=title,
            view_factory=view_factory,
            viewmodel_factory=viewmodel_factory,
            icon_name=entry.get("icon"),
            layout_hint=entry.get("layout_hint"),
        )

    def register(self, descriptor: WidgetModuleDescriptor, *, replace: bool = False) -> None:
        if not descriptor.module_id:
            raise ValueError("module_id is required")
        if descriptor.module_id in self._modules and not replace:
            raise ValueError(f"Module '{descriptor.module_id}' already registered")
        self._modules[descriptor.module_id] = descriptor
        self.changed.emit()

    def list_available(self) -> Iterable[WidgetModuleDescriptor]:
        return list(self._modules.values())

    def get(self, module_id: str) -> WidgetModuleDescriptor | None:
        return self._modules.get(module_id)

    def create_dock(self, module_id: str, dock_id: str) -> ModuleDockItem:
        descriptor = self._modules.get(module_id)
        if not descriptor:
            raise WidgetModuleError(f"Module '{module_id}' is not registered")
        return ModuleDockItem(dock_id, descriptor)


class WidgetHostViewModel(QtCore.QObject):
    """Управляет активными dock-карточками, синхронизирует их с layout."""

    modules_changed = QtCore.Signal(list)

    def __init__(self, registry: WidgetModuleRegistry | None = None) -> None:
        super().__init__()
        self._registry = registry or service_container.try_resolve("widget_module_registry")
        if self._registry is None:
            self._registry = WidgetModuleRegistry()
            service_container.register_singleton(
                "widget_module_registry", lambda: self._registry, replace=True
            )
        try:
            self._registry.load_from_yaml()
        except FileNotFoundError:
            pass
        self._docks: dict[str, ModuleDockItem] = {}

    @property
    def registry(self) -> WidgetModuleRegistry:
        return self._registry

    def ensure_module(self, module_id: str) -> ModuleDockItem:
        dock = self._docks.get(module_id)
        if dock:
            return dock
        dock = self._registry.create_dock(module_id, dock_id=module_id)
        self._docks[module_id] = dock
        dock.closed.connect(lambda mid=module_id: self._remove_dock(mid))
        self.modules_changed.emit(list(self._docks.values()))
        return dock

    def add_module(self, module_id: str) -> ModuleDockItem:
        return self.ensure_module(module_id)

    def load_modules(self, module_ids: Sequence[str]) -> None:
        for module_id in module_ids:
            try:
                self.ensure_module(module_id)
            except WidgetModuleError:
                continue

    def remove_module(self, module_id: str) -> None:
        dock = self._docks.pop(module_id, None)
        if dock:
            dock.cleanup()
            self.modules_changed.emit(list(self._docks.values()))

    def list_active(self) -> list[ModuleDockItem]:
        return list(self._docks.values())

    def _remove_dock(self, module_id: str) -> None:
        self._docks.pop(module_id, None)
        self.modules_changed.emit(list(self._docks.values()))


def _create_registry() -> WidgetModuleRegistry:
    registry = WidgetModuleRegistry()
    try:
        registry.load_from_yaml()
    except FileNotFoundError:
        pass
    return registry


service_container.register_singleton(
    "widget_module_registry",
    _create_registry,
)


service_container.register_singleton(
    "widget_host_viewmodel",
    lambda: WidgetHostViewModel(service_container.resolve("widget_module_registry")),
    replace=True,
)
