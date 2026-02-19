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
        return Path(sys.executable).resolve().parent
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


@cache
def get_stylesheet_path(name: str) -> Path:
    """
    Path to QSS style.

    First tries to find the style in `<root>/src/styles`, then in `<root>/styles`.
    """
    root = get_root_dir()
    candidates = [
        root / "src" / "styles" / name,
        root / "styles" / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Return first candidate by default - calling code will handle missing file
    return candidates[0]


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

