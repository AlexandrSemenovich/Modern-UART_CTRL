"""
Port Manager - thread-safe singleton for tracking active serial ports.
Provides atomic acquire/release operations to prevent race conditions.
"""

import os
import re
import threading
from typing import TypeGuard

SYSTEM_RESERVED_PORTS = set()


def is_valid_port_name(name: object) -> TypeGuard[str]:
    """Type guard to check if name is a valid COM port name.
    
    Args:
        name: Object to check
        
    Returns:
        True if name is a valid COM port string (e.g., 'COM1', 'COM10')
    """
    if not isinstance(name, str):
        return False
    return bool(re.match(r"^COM\d+$", name, re.IGNORECASE))


class PortManager:
    """
    Singleton manager for active serial ports with thread-safe operations.
    
    This replaces the module-level _active_ports set with proper encapsulation
    and atomic operations.
    """
    
    _instance = None
    _lock = threading.Lock()
    _ipc_lock_name = r"Global\\UART_CTRL_PORT_LOCK"
    
    def __new__(cls) -> "PortManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize instance attributes (called after __new__)."""
        if not hasattr(self, '_active_ports'):
            self._active_ports: set[str] = set()
            self._ports_lock = threading.Lock()
            self._system_ports = SYSTEM_RESERVED_PORTS.copy()
            self._ipc_handle = None
            self._setup_ipc_lock()

    def _setup_ipc_lock(self) -> None:
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes

            CreateMutex = ctypes.windll.kernel32.CreateMutexW
            CreateMutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
            CreateMutex.restype = wintypes.HANDLE
            handle = CreateMutex(None, False, self._ipc_lock_name)
            self._ipc_handle = handle
        except Exception:
            self._ipc_handle = None

    def _enter_ipc_lock(self) -> None:
        if os.name != "nt" or not self._ipc_handle:
            return
        import ctypes
        from ctypes import wintypes
        WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
        WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        WaitForSingleObject(self._ipc_handle, 0xFFFFFFFF)

    def _leave_ipc_lock(self) -> None:
        if os.name != "nt" or not self._ipc_handle:
            return
        import ctypes
        from ctypes import wintypes
        ReleaseMutex = ctypes.windll.kernel32.ReleaseMutex
        ReleaseMutex.argtypes = (wintypes.HANDLE,)
        ReleaseMutex(self._ipc_handle)
    
    def _normalize_port_name(self, port_name: object) -> str:
        """Normalize port name preserving custom identifiers."""
        if isinstance(port_name, str) and port_name:
            return port_name
        return str(port_name)

    def acquire(self, port_name: object) -> bool:
        """
        Try to acquire a port for exclusive use.
        
        Args:
            port_name: Name of the port to acquire
            
        Returns:
            True if port was acquired successfully, False if already in use
        """
        normalized = self._normalize_port_name(port_name)
        if normalized is None or normalized in self._system_ports:
            return False

        self._enter_ipc_lock()
        try:
            with self._ports_lock:
                if normalized in self._active_ports:
                    return False
                self._active_ports.add(normalized)
                return True
        finally:
            self._leave_ipc_lock()

    def release(self, port_name: object) -> None:
        """
        Release a previously acquired port.
        
        Args:
            port_name: Name of the port to release
        """
        normalized = self._normalize_port_name(port_name)
        if normalized is None:
            return
        self._enter_ipc_lock()
        try:
            with self._ports_lock:
                self._active_ports.discard(normalized)
        finally:
            self._leave_ipc_lock()

    def is_in_use(self, port_name: object) -> bool:
        """
        Check if a port is currently in use.
        
        Args:
            port_name: Name of the port to check
            
        Returns:
            True if port is in use, False otherwise
        """
        normalized = self._normalize_port_name(port_name)
        if normalized is None:
            return False
        self._enter_ipc_lock()
        try:
            with self._ports_lock:
                return normalized in self._active_ports
        finally:
            self._leave_ipc_lock()
    
    def get_active_ports(self) -> set[str]:
        """
        Get a copy of all currently active ports.
        
        Returns:
            Set of port names that are currently in use
        """
        with self._ports_lock:
            return self._active_ports.copy()
    
    def clear(self) -> None:
        """Clear all active ports (for testing)."""
        with self._ports_lock:
            self._active_ports.clear()


# Global singleton instance
port_manager = PortManager()
