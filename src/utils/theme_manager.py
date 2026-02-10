"""
Theme Manager - handles application theme switching.
Supports light and dark themes with QSettings persistence.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """Singleton manager for application themes."""
    
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
        self.settings = QSettings("UART_CTRL", "ThemeSettings")
        self.load_theme()
    
    def load_theme(self):
        """Load theme from settings."""
        saved_theme = self.settings.value("theme", "dark")
        self.set_theme(saved_theme)
    
    def save_theme(self):
        """Save current theme to settings."""
        self.settings.setValue("theme", self.current_theme)
    
    def set_theme(self, theme: str):
        """Set application theme."""
        if theme not in ["light", "dark", "system"]:
            return False
        
        self.current_theme = theme
        self.apply_theme()
        self.theme_changed.emit(theme)
        self.save_theme()
        return True
    
    def apply_theme(self):
        """Apply current theme to application."""
        app = QApplication.instance()
        if not app:
            return
        
        if self.current_theme == "light":
            self._apply_light_theme(app)
        else:  # dark or system
            self._apply_dark_theme(app)
    
    def _apply_light_theme(self, app):
        """Apply light theme palette."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 100, 255))
        palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
        
        app.setPalette(palette)
    
    def _apply_dark_theme(self, app):
        """Apply dark theme palette."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, QColor(100, 150, 255))
        palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
        
        app.setPalette(palette)
    
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark."""
        return self.current_theme in ["dark", "system"]
    
    def is_light_theme(self) -> bool:
        """Check if current theme is light."""
        return self.current_theme == "light"
    
    def get_theme(self) -> str:
        """Get current theme name."""
        return self.current_theme


# Global theme manager instance
theme_manager = ThemeManager()
