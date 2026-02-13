"""
Theme Manager - handles application theme switching.
Supports light, dark and system themes with QSettings persistence.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor

from src.utils.config_loader import config_loader
from src.utils.paths import get_stylesheet_path


class ThemeManager(QObject):
    """Singleton manager for application themes."""

    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        # Stored logical theme: "light" | "dark" | "system"
        self.current_theme = "dark"
        self.settings = QSettings("UART_CTRL", "ThemeSettings")
        self._stylesheet_cache: str | None = None
        self._last_modified: float = 0.0
        self._qss_path = str(get_stylesheet_path("app.qss"))
        self._logger = logging.getLogger(__name__)
        self._theme_applied = False  # флаг для отслеживания применения темы
        self._last_applied_theme = None  # последняя примененная эффективная тема
        self.load_theme()

    def load_theme(self):
        """Load theme from settings or config default."""
        saved_theme = self.settings.value("theme", None)
        if isinstance(saved_theme, str) and saved_theme in {"light", "dark", "system"}:
            theme = saved_theme
        else:
            # Fallback to config default_theme.theme with validation
            try:
                theme = config_loader.get_default_theme()
            except Exception:  # pragma: no cover - defensive
                theme = "dark"
        self.set_theme(theme)

    def save_theme(self):
        """Save current theme to settings."""
        self.settings.setValue("theme", self.current_theme)

    def set_theme(self, theme: str):
        """Set application theme (light, dark or system)."""
        if theme not in {"light", "dark", "system"}:
            return False

        # Сохраняем тему даже если она не изменилась (для первого запуска)
        theme_changed = theme != self.current_theme
        self.current_theme = theme
        
        # Применяем тему только если QApplication уже создан
        # НЕ применяем здесь, чтобы избежать двойного применения при первом запуске
        # Тема будет применена в main.py через apply_theme(force=True)
        app = QApplication.instance()
        if app and theme_changed:
            # Применяем только если тема действительно изменилась
            self.apply_theme(force=True)
            self.theme_changed.emit(theme)
        
        self.save_theme()
        return True

    # --------- Theme resolution helpers ---------
    def _detect_system_theme(self) -> str:
        """
        Detect current OS theme preference.

        Returns \"light\" or \"dark\". On failure, defaults to \"dark\".
        """
        # Windows: read AppsUseLightTheme from registry
        try:
            if sys.platform.startswith("win"):
                settings = QSettings(
                    r"HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                    QSettings.NativeFormat,
                )
                value = settings.value("AppsUseLightTheme", 1, int)
                return "light" if int(value) != 0 else "dark"
        except Exception:
            # If anything goes wrong we just fall back below
            pass

        # Fallback for other OS / unknown: prefer dark as more neutral for terminals
        return "dark"

    def _get_effective_theme(self) -> str:
        """
        Resolve logical theme (light/dark/system) into concrete \"light\" or \"dark\".
        """
        if self.current_theme == "system":
            return self._detect_system_theme()
        return "light" if self.current_theme == "light" else "dark"

    def apply_theme(self, force: bool = False):
        """
        Apply current theme (or resolved system theme) to application.
        
        Args:
            force: If True, apply theme even if it was already applied.
        """
        app = QApplication.instance()
        if not app:
            # Если QApplication ещё не создан, просто сохраняем тему
            # Она будет применена позже при создании app
            return

        effective = self._get_effective_theme()
        
        # Предотвращаем двойное применение той же темы
        # Проверяем, была ли уже применена та же эффективная тема
        if self._theme_applied and not force:
            if self._last_applied_theme == effective:
                # Та же тема уже применена, не применяем повторно
                return

        # Применяем тему только если она изменилась или принудительно
        if effective == "light":
            self._apply_light_theme(app)
        else:
            self._apply_dark_theme(app)

        # themeClass используется в QSS-селекторах
        app.setProperty("themeClass", effective)
        self._apply_stylesheet(app)
        self._theme_applied = True
        self._last_applied_theme = effective  # сохраняем последнюю примененную тему

    def _apply_light_theme(self, app: QApplication) -> None:
        """Apply light theme palette: бело-синие аккуратные оттенки."""
        palette = QPalette()
        # Основной фон окна и панелей
        palette.setColor(QPalette.Window, QColor("#f4f6fb"))  # мягкий светлый синий/серый
        palette.setColor(QPalette.Base, QColor("#ffffff"))    # фон полей ввода/текста
        # Текст
        palette.setColor(QPalette.WindowText, QColor("#0f172a"))
        palette.setColor(QPalette.Text, QColor("#0f172a"))
        # Кнопки
        palette.setColor(QPalette.Button, QColor("#e3edff"))
        palette.setColor(QPalette.ButtonText, QColor("#0f172a"))
        # Ссылки и акцент
        palette.setColor(QPalette.Link, QColor("#2563eb"))       # насыщенный синий
        palette.setColor(QPalette.Highlight, QColor("#2563eb"))  # выбор/выделение
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

        app.setPalette(palette)

    def _apply_dark_theme(self, app: QApplication) -> None:
        """Apply dark theme palette: темно-синий + чёрный."""
        palette = QPalette()
        # Глубокий тёмный фон с лёгким синим оттенком
        palette.setColor(QPalette.Window, QColor("#020617"))  # почти чёрный синий
        palette.setColor(QPalette.Base, QColor("#020617"))
        # Текст
        palette.setColor(QPalette.WindowText, QColor("#e5e7eb"))
        palette.setColor(QPalette.Text, QColor("#e5e7eb"))
        # Кнопки и вторичные поверхности
        palette.setColor(QPalette.Button, QColor("#020617"))
        palette.setColor(QPalette.ButtonText, QColor("#e5e7eb"))
        # Ссылки и акцент
        palette.setColor(QPalette.Link, QColor("#60a5fa"))
        palette.setColor(QPalette.Highlight, QColor("#1d4ed8"))      # тёмный насыщенный синий
        palette.setColor(QPalette.HighlightedText, QColor("#f9fafb"))

        app.setPalette(palette)

    def _apply_stylesheet(self, app):
        """Ensure the global QSS is loaded and applied with cache invalidation."""
        # Check if stylesheet file has been modified
        try:
            import os

            current_modified = os.path.getmtime(self._qss_path)
        except OSError:
            current_modified = 0.0
        
        # Invalidate cache if file changed or theme requires fresh load
        if (
            self._stylesheet_cache is None or
            current_modified > self._last_modified
        ):
            self._stylesheet_cache = self._load_stylesheet()
            self._last_modified = current_modified

        if self._stylesheet_cache:
            themed_stylesheet = self._format_stylesheet(self._stylesheet_cache)
            app.setStyleSheet(themed_stylesheet)

    def _load_stylesheet(self) -> str:
        """Load application stylesheet from disk."""
        try:
            with open(self._qss_path, "r", encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            self._logger.warning(
                "Failed to load stylesheet from %s: %s", self._qss_path, exc
            )
            return ""

    def _format_stylesheet(self, template: str) -> str:
        """Inject theme-specific color values into the stylesheet template."""
        theme = "light" if self.current_theme == "light" else "dark"
        button_colors = config_loader.get_button_colors(theme)
        palette = {
            "$command_combo_active": button_colors.command_combo_active,
            "$command_combo_connecting": button_colors.command_combo_connecting,
            "$command_combo_inactive": button_colors.command_combo_inactive,
            "$command_cpu1_active": button_colors.command_cpu1_active,
            "$command_cpu1_connecting": button_colors.command_cpu1_connecting,
            "$command_cpu1_inactive": button_colors.command_cpu1_inactive,
            "$command_cpu2_active": button_colors.command_cpu2_active,
            "$command_cpu2_connecting": button_colors.command_cpu2_connecting,
            "$command_cpu2_inactive": button_colors.command_cpu2_inactive,
            "$command_tlm_active": button_colors.command_tlm_active,
            "$command_tlm_connecting": button_colors.command_tlm_connecting,
            "$command_tlm_inactive": button_colors.command_tlm_inactive,
            "$command_text_active": button_colors.command_text_active,
            "$command_text_connecting": button_colors.command_text_connecting,
            "$command_text_inactive": button_colors.command_text_inactive,
        }

        themed = template
        for token, value in palette.items():
            themed = themed.replace(token, value)
        return themed

    def is_dark_theme(self) -> bool:
        """Check if current effective theme is dark."""
        return self._get_effective_theme() == "dark"
    
    def is_light_theme(self) -> bool:
        """Check if current effective theme is light."""
        return self._get_effective_theme() == "light"
    
    def get_theme(self) -> str:
        """Get current theme name."""
        return self.current_theme


# Global theme manager instance
theme_manager = ThemeManager()
