"""Thread-safe service container for dependency injection."""

from __future__ import annotations

from typing import Callable, Dict, Any
import threading


class ServiceContainer:
    """Minimalistic service locator with singleton registration."""

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_singleton(self, key: str, factory: Callable[[], Any], *, replace: bool = False) -> None:
        """Register singleton factory under key. Optionally replace existing."""
        with self._lock:
            if key in self._factories and not replace:
                raise ValueError(f"Service '{key}' already registered")
            self._factories[key] = factory
            if replace and key in self._instances:
                # Drop existing instance to force recreation on next resolve
                del self._instances[key]

    def resolve(self, key: str) -> Any:
        """Get singleton instance, creating via factory on first call."""
        with self._lock:
            if key in self._instances:
                return self._instances[key]
            if key not in self._factories:
                raise KeyError(f"Service '{key}' is not registered")
            instance = self._factories[key]()
            self._instances[key] = instance
            return instance

    def try_resolve(self, key: str) -> Any | None:
        """Resolve service if registered, otherwise return None."""
        with self._lock:
            if key in self._instances:
                return self._instances[key]
            factory = self._factories.get(key)
            if not factory:
                return None
            instance = factory()
            self._instances[key] = instance
            return instance


service_container = ServiceContainer()
