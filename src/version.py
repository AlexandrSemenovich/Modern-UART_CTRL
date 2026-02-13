"""
Project version helper.

Версия берётся из конфигурации приложения ([app] section в config.ini),
что делает запуск независимым от наличия git и ускоряет холодный старт.
"""

from src.utils.config_loader import config_loader

__version__ = config_loader.get_app_version()


def get_version() -> str:
    """Return application version string."""
    return __version__
