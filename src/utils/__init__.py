"""Utilities package with shared services."""

from src.utils.service_container import service_container
from src.utils.config_loader import ConfigLoader
from src.utils.theme_manager import ThemeManager
from src.utils.quick_blocks_repository import QuickBlocksRepository


def get_theme_manager() -> ThemeManager:
    """Resolve global theme manager instance via service container."""
    return service_container.resolve("theme_manager")


def get_config_loader() -> ConfigLoader:
    """Resolve global config loader from service container."""
    return service_container.resolve("config_loader")


def get_quick_blocks_repository() -> QuickBlocksRepository:
    """Resolve Quick Blocks repository instance."""
    return service_container.resolve("quick_blocks_repository")
