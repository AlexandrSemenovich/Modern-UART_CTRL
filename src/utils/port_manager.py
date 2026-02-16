"""
Port Manager - thread-safe singleton for tracking active serial ports.
Provides atomic acquire/release operations to prevent race conditions.
"""

import threading
from typing import Set


class PortManager:
    """
    Singleton manager for active serial ports with thread-safe operations.
    
    This replaces the module-level _active_ports set with proper encapsulation
    and atomic operations.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "PortManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._active_ports: Set[str] = set()
                    cls._instance._ports_lock = threading.Lock()
        return cls._instance
    
    def acquire(self, port_name: str) -> bool:
        """
        Try to acquire a port for exclusive use.
        
        Args:
            port_name: Name of the port to acquire
            
        Returns:
            True if port was acquired successfully, False if already in use
        """
        with self._ports_lock:
            if port_name in self._active_ports:
                return False
            self._active_ports.add(port_name)
            return True
    
    def release(self, port_name: str) -> None:
        """
        Release a previously acquired port.
        
        Args:
            port_name: Name of the port to release
        """
        with self._ports_lock:
            self._active_ports.discard(port_name)
    
    def is_in_use(self, port_name: str) -> bool:
        """
        Check if a port is currently in use.
        
        Args:
            port_name: Name of the port to check
            
        Returns:
            True if port is in use, False otherwise
        """
        with self._ports_lock:
            return port_name in self._active_ports
    
    def get_active_ports(self) -> Set[str]:
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
