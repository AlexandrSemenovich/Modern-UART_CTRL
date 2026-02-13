"""
Пути и директории приложения.

Цели:
- Единая точка вычисления корня проекта и директории конфигурации.
- Поддержка как режима разработки, так и упакованных сборок (PyInstaller и т.п.).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_frozen() -> bool:
    """Определить, запущено ли приложение в упакованном виде (PyInstaller и т.п.)."""
    return bool(getattr(sys, "frozen", False))


def get_root_dir() -> Path:
    """
    Корень проекта/приложения.

    - В режиме разработки: корневая папка репозитория.
    - В упакованном виде: директория исполняемого файла.
    """
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    # src/utils/paths.py -> parents[2] == корень проекта
    return Path(__file__).resolve().parents[2]


def get_config_dir() -> Path:
    """
    Директория конфигурации.

    Приоритет:
    1. Переменная окружения UART_CTRL_CONFIG_DIR (для явного переопределения).
    2. Для упакованного приложения:
       - Windows: %APPDATA%/UART_CTRL
       - Остальные: ~/.config/uart_ctrl
    3. Для разработки: <root>/config
    """
    env_dir = os.environ.get("UART_CTRL_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    if _is_frozen():
        if sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or str(get_root_dir())
            return Path(base) / "UART_CTRL"
        # POSIX-подобные системы
        home = Path(os.path.expanduser("~"))
        return home / ".config" / "uart_ctrl"

    # Режим разработки: конфиг рядом с исходниками
    return get_root_dir() / "config"


def ensure_dir(path: Path) -> None:
    """Гарантировать наличие директории для указанного пути к файлу."""
    path.parent.mkdir(parents=True, exist_ok=True)


def get_config_file(name: str) -> Path:
    """Полный путь к конфигурационному файлу в каталоге конфигурации."""
    cfg_dir = get_config_dir()
    cfg_path = cfg_dir / name
    ensure_dir(cfg_path)
    return cfg_path


def get_stylesheet_path(name: str) -> Path:
    """
    Путь к QSS‑стилю.

    Пытается сначала найти стиль в `<root>/src/styles`, затем в `<root>/styles`.
    """
    root = get_root_dir()
    candidates = [
        root / "src" / "styles" / name,
        root / "styles" / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Возвращаем первый кандидат по умолчанию — вызывающий код сам обработает отсутствие файла
    return candidates[0]

