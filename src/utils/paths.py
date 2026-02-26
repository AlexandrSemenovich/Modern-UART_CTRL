"""
Paths and directories of the application.

Goals:
- Single point of computation for project root and configuration directory.
- Support both development mode and packed builds (PyInstaller, etc.).
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from functools import cache
from importlib import resources
import shutil
from pathlib import Path
from typing import Generator, TextIO


@cache
def _is_frozen() -> bool:
    """Determine if the application is running in packed form (PyInstaller, etc.)."""
    return bool(getattr(sys, "frozen", False))


@cache
def get_root_dir() -> Path:
    """
    Project/application root.

    - In development mode: repository root folder.
    - In packed form: executable file directory.
    """
    if _is_frozen():
        if hasattr(sys, "_MEIPASS"):
            return Path(getattr(sys, "_MEIPASS"))
        exe_dir = Path(sys.executable).resolve().parent
        # PyInstaller on Windows keeps resources inside `_internal`, so prefer it if present
        internal = exe_dir / "_internal"
        if internal.exists():
            return internal
        return exe_dir
    # src/utils/paths.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


@cache
def get_config_dir() -> Path:
    """
    Configuration directory.

    Priority:
    1. UART_CTRL_CONFIG_DIR environment variable (for explicit override).
    2. For packed application:
       - Windows: %APPDATA%/UART_CTRL
       - Others: ~/.config/uart_ctrl
    3. For development: <root>/config
    """
    env_dir = os.environ.get("UART_CTRL_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    if _is_frozen():
        if sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or str(get_root_dir())
            return Path(base) / "UART_CTRL"
        # POSIX-like systems
        home = Path(os.path.expanduser("~"))
        return home / ".config" / "uart_ctrl"

    # Development mode: config next to sources
    return get_root_dir() / "config"


def ensure_dir(path: Path) -> None:
    """Guarantee the existence of a directory for the specified file path."""
    path.parent.mkdir(parents=True, exist_ok=True)


@cache
def get_config_file(name: str) -> Path:
    """Full path to a configuration file in the configuration directory."""
    cfg_dir = get_config_dir()
    cfg_path = cfg_dir / name
    ensure_dir(cfg_path)
    return cfg_path

def _resolve_candidate(path: Path, name: str) -> Path | None:
    if path.is_file():
        return path
    if path.is_dir():
        nested = path / name
        if nested.is_file():
            return nested
    return None


def _find_stylesheet_source(name: str) -> Path | None:
    exe_dir = Path(sys.executable).resolve().parent
    candidates: list[Path]
    if _is_frozen():
        meipass = get_root_dir()
        candidates = [
            exe_dir / "styles" / name,
            meipass / "styles" / name,
            meipass / "src" / "styles" / name,
        ]
    else:
        root = get_root_dir()
        candidates = [
            root / "src" / "styles" / name,
            root / "styles" / name,
        ]
    for candidate in candidates:
        resolved = _resolve_candidate(candidate, name)
        if resolved:
            return resolved
    return None


def _load_stylesheet_bytes(name: str) -> bytes | None:
    try:
        return resources.read_binary("src.styles", name)
    except (FileNotFoundError, ModuleNotFoundError):
        return None


def _copy_stylesheet(source: Path, target: Path) -> bool:
    try:
        shutil.copy2(source, target)
        return True
    except PermissionError:
        try:
            data = source.read_bytes()
        except OSError:
            return False
        target.write_bytes(data)
        return True
    except OSError:
        return False


def _ensure_stylesheet(name: str) -> Path:
    target_dir = get_config_dir() / "styles"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / name
    if target_path.exists():
        return target_path

    source = _find_stylesheet_source(name)
    if source and source.exists():
        if _copy_stylesheet(source, target_path):
            return target_path

    data = _load_stylesheet_bytes(name)
    if data is not None:
        target_path.write_bytes(data)
    return target_path


@cache
def get_stylesheet_path(name: str) -> Path:
    """
    Path to QSS style.

    First tries to find the style in `<root>/src/styles`, then in `<root>/styles`.
    """
    if not _is_frozen():
        source = _find_stylesheet_source(name)
        if source:
            return source
    return _ensure_stylesheet(name)


@contextmanager
def open_config_file(name: str, mode: str = 'r') -> Generator[TextIO, None, None]:
    """Context manager for safely opening configuration files.
    
    Args:
        name: Configuration file name
        mode: File open mode ('r', 'w', 'a')
        
    Yields:
        File handle for the configuration file
        
    Example:
        with open_config_file('settings.ini', 'r') as f:
            content = f.read()
    """
    cfg_path = get_config_file(name)
    ensure_dir(cfg_path.parent)
    
    with open(cfg_path, mode, encoding='utf-8') as f:
        yield f


@contextmanager
def open_stylesheet(name: str, mode: str = 'r') -> Generator[TextIO, None, None]:
    """Context manager for safely opening stylesheet files.
    
    Args:
        name: Stylesheet file name
        mode: File open mode ('r', 'w', 'a')
        
    Yields:
        File handle for the stylesheet file
        
    Example:
        with open_stylesheet('theme.qss', 'r') as f:
            stylesheet = f.read()
    """
    style_path = get_stylesheet_path(name)
    ensure_dir(style_path.parent)
    
    with open(style_path, mode, encoding='utf-8') as f:
        yield f

