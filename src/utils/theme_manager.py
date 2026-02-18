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
        self.current_theme = "light"
        self.settings = QSettings("UART_CTRL", "ThemeSettings")
        self._stylesheet_cache: str | None = None
        self._last_modified: float = 0.0
        self._qss_path = str(get_stylesheet_path("app_optimized.qss"))
        self._logger = logging.getLogger(__name__)
        self._theme_applied = False      # flag for tracking theme application
        self._last_applied_theme = None  # last applied effective theme
        self._last_logical_theme = None  # last logical theme
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
        
        # If theme is "system", immediately determine effective theme for consistent application
        # This prevents visual artifacts on first launch with system theme
        if theme == "system":
            # Forcibly apply theme with system theme detection
            self.set_theme(theme)
        else:
            self.set_theme(theme)

    def save_theme(self):
        """Save current theme to settings."""
        self.settings.setValue("theme", self.current_theme)

    def set_theme(self, theme: str):
        """Set application theme (light, dark or system)."""
        if theme not in {"light", "dark", "system"}:
            return False

        # Always save and apply theme - this ensures full redraw
        # On any theme change (including switching between explicit themes)
        old_theme = self.current_theme
        self.current_theme = theme
        
        # Apply theme only if QApplication is already created
        app = QApplication.instance()
        if app:
            # Always apply theme for full redraw of all elements
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
            # If QApplication is not yet created, just save the theme
            # It will be applied later when app is created
            return

        effective = self._get_effective_theme()
        logical = self.current_theme
        
        # Prevent double application of the same theme
        # Check if the same effective theme has already been applied
        # Ignore if logical theme changes (e.g., light->system)
        if self._theme_applied and not force:
            if self._last_applied_theme == effective and logical == self._last_logical_theme:
                # Same theme already applied, don't apply again
                return

        # Apply theme only if it changed or forced
        if effective == "light":
            self._apply_light_theme(app)
        else:
            self._apply_dark_theme(app)

        # themeClass is used in QSS selectors
        # Always set on app - this is important for correct style application
        app.setProperty("themeClass", effective)
        
        # Apply stylesheet
        self._apply_stylesheet(app)
        
        # Update state
        self._theme_applied = True
        self._last_applied_theme = effective  # save last applied theme
        self._last_logical_theme = logical  # save last logical theme

    def _apply_light_theme(self, app: QApplication) -> None:
        """Apply light theme palette: white-blue clean shades."""
        colors = config_loader.get_palette_colors("light")
        palette = QPalette()
        # Main background for windows and panels
        palette.setColor(QPalette.Window, QColor(colors.window))
        palette.setColor(QPalette.Base, QColor(colors.base))
        # Text
        palette.setColor(QPalette.WindowText, QColor(colors.window_text))
        palette.setColor(QPalette.Text, QColor(colors.text))
        # Buttons
        palette.setColor(QPalette.Button, QColor(colors.button))
        palette.setColor(QPalette.ButtonText, QColor(colors.button_text))
        # Links and accent
        palette.setColor(QPalette.Link, QColor(colors.link))
        palette.setColor(QPalette.Highlight, QColor(colors.highlight))
        palette.setColor(QPalette.HighlightedText, QColor(colors.highlighted_text))

        # Additional colors for palette-based QSS
        palette.setColor(QPalette.Mid, QColor("#d0d7e6"))
        palette.setColor(QPalette.Midlight, QColor("#e5e7eb"))
        palette.setColor(QPalette.Light, QColor("#ffffff"))
        palette.setColor(QPalette.Dark, QColor("#c0c5ce"))
        palette.setColor(QPalette.AlternateBase, QColor("#f3f4f7"))

        app.setPalette(palette)

    def _apply_dark_theme(self, app: QApplication) -> None:
        """Apply dark theme palette: dark blue + black."""
        colors = config_loader.get_palette_colors("dark")
        palette = QPalette()
        # Deep dark background with slight blue tint
        palette.setColor(QPalette.Window, QColor(colors.window))
        palette.setColor(QPalette.Base, QColor(colors.base))
        # Text
        palette.setColor(QPalette.WindowText, QColor(colors.window_text))
        palette.setColor(QPalette.Text, QColor(colors.text))
        # Buttons and secondary surfaces
        palette.setColor(QPalette.Button, QColor(colors.button))
        palette.setColor(QPalette.ButtonText, QColor(colors.button_text))
        # Links and accent
        palette.setColor(QPalette.Link, QColor(colors.link))
        palette.setColor(QPalette.Highlight, QColor(colors.highlight))
        palette.setColor(QPalette.HighlightedText, QColor(colors.highlighted_text))

        # Additional colors for palette-based QSS
        palette.setColor(QPalette.Mid, QColor("#374151"))
        palette.setColor(QPalette.Midlight, QColor("#4b5563"))
        palette.setColor(QPalette.Light, QColor("#1f2937"))
        palette.setColor(QPalette.Dark, QColor("#111827"))
        palette.setColor(QPalette.AlternateBase, QColor("#0f172a"))

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
        # Use effective theme, not logical (system can be light or dark)
        theme = self._get_effective_theme()
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
