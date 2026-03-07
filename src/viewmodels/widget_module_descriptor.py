"""Shared dataclass for widget host module descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6 import QtCore, QtWidgets


@dataclass(slots=True)
class WidgetModuleDescriptor:
    """Метаданные зарегистрированного модуля виджет-хоста."""

    module_id: str
    title: str
    view_factory: Callable[[QtWidgets.QWidget | None, QtCore.QObject | None], QtWidgets.QWidget]
    viewmodel_factory: Callable[[], QtCore.QObject | None] | None = None
    icon_name: str | None = None
    layout_hint: dict | None = None


__all__ = ["WidgetModuleDescriptor"]
