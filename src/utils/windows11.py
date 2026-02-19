"""
Windows 11 integration utilities for modern UI effects.

Provides:
- Rounded window corners
- Mica backdrop effect (Windows 11 only)
- Dark/light theme detection
- Global system hotkeys
"""

import sys
import ctypes
from ctypes import wintypes
from functools import cache
from typing import Optional, Callable, Dict, List

# Windows API constants
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_CORNER_RADIUS = 33

# Backdrop types
DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_TRANSIENTWINDOW = 2
DWMSBT_TABBEDWINDOW = 3
DWMSBT_TABBED = 3  # Alias for convenience
DWMSBT_MICA = 4  # Windows 11 only

# Corner radius values
WIN11_CORNER_ROUND = 8
WIN10_CORNER_ROUND = 2

# Hotkey constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312


@cache
def is_windows_11_or_later() -> bool:
    """Check if running on Windows 11 or later."""
    try:
        version = sys.getwindowsversion()
        # Windows 11 starts at build 22000
        return version.build >= 22000
    except Exception:
        return False


def _get_dwmapi_dll() -> Optional[ctypes.CDLL]:
    """Get dwmapi.dll handle."""
    try:
        return ctypes.windll.dwmapi
    except Exception:
        return None


def set_window_rounded_corners(hwnd: int, radius: int = WIN11_CORNER_ROUND) -> bool:
    """
    Set rounded corners for a window.
    
    Args:
        hwnd: Window handle
        radius: Corner radius in pixels (8 for Win11, 2 for Win10)
    
    Returns:
        True if successful, False otherwise
    """
    if not hwnd:
        return False
    
    dwm = _get_dwmapi_dll()
    if not dwm:
        return False
    
    try:
        # Set corner radius
        result = dwm.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CORNER_RADIUS,
            ctypes.byref(ctypes.c_int(radius)),
            ctypes.sizeof(ctypes.c_int)
        )
        return result == 0
    except Exception:
        return False


def set_window_backdrop(hwnd: int, backdrop_type: int = DWMSBT_MICA) -> bool:
    """
    Set backdrop effect for a window (Windows 11 only).
    
    Args:
        hwnd: Window handle
        backdrop_type: One of DWMSBT_* constants
    
    Returns:
        True if successful, False otherwise
    """
    if not hwnd:
        return False
    
    if not is_windows_11_or_later():
        # Silently skip on Windows 10 - Mica is not supported
        return False
    
    dwm = _get_dwmapi_dll()
    if not dwm:
        return False
    
    try:
        result = dwm.DwmSetWindowAttribute(
            hwnd,
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(backdrop_type)),
            ctypes.sizeof(ctypes.c_int)
        )
        return result == 0
    except Exception:
        return False
    if not hwnd:
        return False
    
    # Only Windows 11 supports Mica
    if not is_windows_11_or_later():
        return False
    
    dwm = _get_dwmapi_dll()
    if not dwm:
        return False
    
    try:
        result = dwm.DwmSetWindowAttribute(
            hwnd,
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(backdrop_type)),
            ctypes.sizeof(ctypes.c_int)
        )
        return result == 0
    except Exception:
        return False


def set_immersive_dark_mode(hwnd: int, enabled: bool = True) -> bool:
    """
    Enable/disable immersive dark mode for a window.
    
    Args:
        hwnd: Window handle
        enabled: True for dark mode, False for light mode
    
    Returns:
        True if successful, False otherwise
    """
    if not hwnd:
        return False
    
    dwm = _get_dwmapi_dll()
    if not dwm:
        return False
    
    try:
        result = dwm.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1 if enabled else 0)),
            ctypes.sizeof(ctypes.c_int)
        )
        return result == 0
    except Exception:
        return False


def apply_windows_11_style(hwnd: int, is_dark_theme: bool = True) -> bool:
    """
    Apply Windows 11 visual style to a window.
    
    Args:
        hwnd: Window handle
        is_dark_theme: Whether dark theme is active
    
    Returns:
        True if successful, False otherwise
    """
    if not hwnd:
        return False
    
    success = False
    
    # Set rounded corners
    radius = WIN11_CORNER_ROUND if is_windows_11_or_later() else WIN10_CORNER_ROUND
    if set_window_rounded_corners(hwnd, radius):
        success = True
    
    # Try to set Mica backdrop (Windows 11 only)
    if is_windows_11_or_later():
        # Use TABBED for better compatibility, or TRANSIENT for dialogs
        if set_window_backdrop(hwnd, DWMSBT_TABBED):
            success = True
    
    # Set dark/light mode
    if set_immersive_dark_mode(hwnd, is_dark_theme):
        success = True
    
    return success


class GlobalHotkeyManager:
    """
    Manager for global system-wide hotkeys using Windows API.
    
    Allows registering hotkeys that work even when the application
    is not in focus.
    """
    
    def __init__(self, hwnd: int):
        """
        Initialize the hotkey manager.
        
        Args:
            hwnd: Window handle to receive hotkey messages
        """
        self._hwnd = hwnd
        self._hotkeys: Dict[int, Callable] = {}
        self._next_id = 1
        self._user32 = None
        
        # Try to load user32.dll
        try:
            self._user32 = ctypes.windll.user32
        except Exception:
            pass
    
    def register_hotkey(
        self, 
        key: int, 
        modifiers: int, 
        callback: Callable
    ) -> Optional[int]:
        """
        Register a global hotkey.
        
        Args:
            key: Virtual key code (e.g., 0x41 for 'A')
            modifiers: Modifier flags (MOD_CONTROL, MOD_ALT, etc.)
            callback: Function to call when hotkey is pressed
        
        Returns:
            Hotkey ID if successful, None otherwise
        """
        if not self._user32 or not self._hwnd:
            return None
        
        hotkey_id = self._next_id
        self._next_id += 1
        
        # Register the hotkey
        result = self._user32.RegisterHotKey(
            self._hwnd,
            hotkey_id,
            modifiers | MOD_NOREPEAT,
            key
        )
        
        if result:
            self._hotkeys[hotkey_id] = callback
            return hotkey_id
        
        return None
    
    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """
        Unregister a global hotkey.
        
        Args:
            hotkey_id: ID returned by register_hotkey
        
        Returns:
            True if successful
        """
        if not self._user32 or hotkey_id not in self._hotkeys:
            return False
        
        result = self._user32.UnregisterHotKey(self._hwnd, hotkey_id)
        if result:
            del self._hotkeys[hotkey_id]
        
        return bool(result)
    
    def handle_message(self, wparam: int) -> bool:
        """
        Handle a WM_HOTKEY message.
        
        Args:
            wparam: The wParam from the message
        
        Returns:
            True if the message was handled
        """
        if wparam in self._hotkeys:
            callback = self._hotkeys[wparam]
            callback()
            return True
        return False
    
    def cleanup(self) -> None:
        """Unregister all hotkeys."""
        if self._user32:
            for hotkey_id in list(self._hotkeys.keys()):
                self._user32.UnregisterHotKey(self._hwnd, hotkey_id)
        self._hotkeys.clear()


# Virtual key codes for common keys
class VK:
    """Virtual key codes."""
    SPACE = 0x20
    ENTER = 0x0D
    TAB = 0x09
    ESCAPE = 0x1B
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A
    NUM0 = 0x30
    NUM1 = 0x31
    NUM2 = 0x32
    NUM3 = 0x33
    NUM4 = 0x34
    NUM5 = 0x35
    NUM6 = 0x36
    NUM7 = 0x37
    NUM8 = 0x38
    NUM9 = 0x39
