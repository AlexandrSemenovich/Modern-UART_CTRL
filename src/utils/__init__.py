"""Utilities package with shared services."""

from src.utils.service_container import service_container
from src.utils.config_loader import ConfigLoader
from src.utils.theme_manager import ThemeManager


def get_theme_manager() -> ThemeManager:
    """Resolve global theme manager instance via service container."""
    return service_container.resolve("theme_manager")


def get_config_loader() -> ConfigLoader:
    """Resolve global config loader from service container."""
    return service_container.resolve("config_loader")
