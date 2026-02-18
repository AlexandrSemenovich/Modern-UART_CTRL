"""
Icon Cache - centralized icon management for the application.
Supports theme-aware icons, caching, DPI scaling, and automatic theme switching.

Icon naming convention in assets/icons/fa/:
- {name}.svg         - neutral icon (used as fallback)
- {name}_light.svg  - icon for light theme
- {name}_dark.svg   - icon for dark theme
- {name}_light.ico  - Windows ICO for light theme
- {name}_dark.ico   - Windows ICO for dark theme
"""

import logging
import os
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap, QPainter, QIconEngine, QImage, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from src.utils.theme_manager import ThemeManager
from src.utils.paths import get_root_dir


class IconCache(QObject):
    """
    Singleton icon cache with theme awareness and DPI scaling support.
    
    Features:
    - Automatic theme-based icon switching
    - Caching for performance
    - DPI scaling support
    - Fallback icons
    - Signal-based theme change notifications
    """
    
    # Signal emitted when icon is updated (theme change)
    icon_updated = Signal(str, QIcon)  # icon_name, new_icon
    
    _instance: Optional['IconCache'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'IconCache':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if IconCache._initialized:
            return
            
        super().__init__()
        IconCache._initialized = True
        
        self._logger = logging.getLogger(__name__)
        self._icon_cache: dict[str, QIcon] = {}
        self._theme_suffix_cache: dict[str, str] = {}  # theme -> suffix mapping
        
        # Get base icons directory
        self._base_icons_dir = self._get_icons_directory()
        
        # Connect to theme manager
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        self._logger.info(f"IconCache initialized. Base directory: {self._base_icons_dir}")
    
    def _get_icons_directory(self) -> str:
        """Get the base icons directory path."""
        # Use project's get_root_dir() for proper path resolution
        root_dir = get_root_dir()
        icons_dir = root_dir / "assets" / "icons"
        icons_dir_str = str(icons_dir)
        
        if not os.path.exists(icons_dir_str):
            self._logger.warning(f"Icons directory not found: {icons_dir_str}")
            
        return icons_dir_str
    
    def _get_dpi_scale_factor(self) -> float:
        """Get the current DPI scale factor."""
        app = QApplication.instance()
        if not app:
            return 1.0
            
        primary_screen = app.primaryScreen()
        if not primary_screen:
            return 1.0
            
        # Get logical DPI and calculate scale factor
        try:
            # PySide6 uses different method names
            logical_dpi = primary_screen.logicalDotsPerYInch()
        except AttributeError:
            try:
                logical_dpi = primary_screen.logicalDpiY()
            except AttributeError:
                return 1.0
        
        # Standard DPI is 96, scale factor = current / 96
        return logical_dpi / 96.0
    
    def _get_theme_suffix(self, theme: str) -> str:
        """
        Get the appropriate suffix for the current theme.
        
        For fa/ icons: _dark, _light (e.g., clock-rotate-left_dark.svg)
        For root icons: _black, _white (e.g., icon_black.ico)
        
        Args:
            theme: "light" or "dark"
            
        Returns:
            Suffix string
        """
        if theme == "dark":
            return "_dark"
        elif theme == "light":
            return "_light"
        return ""  # neutral
    
    def _resolve_icon_path(self, name: str, theme: str) -> Optional[str]:
        """
        Resolve the full path to an icon file.
        
        New folder-based structure (preferred):
        - assets/icons/light/{name}.svg (or .ico)
        - assets/icons/dark/{name}.svg (or .ico)
        
        Legacy suffix-based structure (fallback):
        - assets/icons/fa/{name}_light.svg
        - assets/icons/fa/{name}_dark.svg
        - assets/icons/fa/{name}.svg
        
        Args:
            name: Icon name without extension and theme suffix
            theme: "light" or "dark"
            
        Returns:
            Full path to icon file or None if not found
        """
        # ==== Check folder-based structure first (new format) ====
        theme_folder = theme  # "light" or "dark"
        extensions = [".svg", ".ico", ".png", ".jpg"]
        
        for ext in extensions:
            folder_path = os.path.join(self._base_icons_dir, theme_folder, f"{name}{ext}")
            if os.path.exists(folder_path):
                return folder_path
        
        # ==== Check fa/ subdirectory with theme suffixes (legacy format) ====
        theme_suffix = self._get_theme_suffix(theme)
        
        # Try theme-specific icon in fa/
        for ext in [".svg"]:
            themed_name = f"{name}{theme_suffix}{ext}"
            fa_path = os.path.join(self._base_icons_dir, "fa", themed_name)
            if os.path.exists(fa_path):
                return fa_path
        
        # Fallback to neutral in fa/
        for ext in [".svg"]:
            neutral_name = f"{name}{ext}"
            fa_path = os.path.join(self._base_icons_dir, "fa", neutral_name)
            if os.path.exists(fa_path):
                return fa_path
        
        # ==== Special case: icon in root directory (legacy ICO files) ====
        if name == "icon":
            if theme == "dark":
                ico_name = "icon_black.ico"
            else:
                ico_name = "icon_white.ico"
            root_path = os.path.join(self._base_icons_dir, ico_name)
            if os.path.exists(root_path):
                return root_path
        
        self._logger.warning(f"Icon not found: {name} (theme: {theme})")
        return None
    
    def _load_icon(self, name: str, theme: str) -> QIcon:
        """
        Load an icon from file with DPI scaling.
        
        Args:
            name: Icon name (e.g., "clock-rotate-left")
            theme: "light" or "dark"
            
        Returns:
            Loaded QIcon with proper scaling
        """
        icon_path = self._resolve_icon_path(name, theme)
        
        if icon_path is None:
            # Return empty icon as fallback
            return QIcon()
        
        # Get DPI scale factor
        scale_factor = self._get_dpi_scale_factor()
        
        # Load the icon
        icon = QIcon(icon_path)
        
        # If SVG, we might need to specify size for proper scaling
        if icon_path.endswith(".svg") and scale_factor != 1.0:
            # For SVG, Qt handles scaling automatically when using pixmap()
            # But we can set the icon size hints
            icon.setThemeName("")  # Clear any system theme
        
        return icon
    
    def get(self, name: str) -> QIcon:
        """
        Get an icon by name, automatically selecting theme-appropriate version.
        
        This is the main entry point for getting icons.
        
        Args:
            name: Icon name (e.g., "clock-rotate-left", "icon")
            
        Returns:
            Theme-aware QIcon
        """
        # Determine current effective theme
        theme = self._theme_manager._get_effective_theme()
        
        # Create cache key with theme
        cache_key = f"{name}:{theme}"
        
        # Check cache first
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # Load and cache
        icon = self._load_icon(name, theme)
        self._icon_cache[cache_key] = icon
        
        return icon
    
    def get_explicit(self, name: str, theme: str) -> QIcon:
        """
        Get an icon with explicit theme specification.
        
        Use this when you need a specific theme version.
        
        Args:
            name: Icon name
            theme: "light", "dark", or "neutral"
            
        Returns:
            QIcon for the specified theme
        """
        effective_theme = "dark" if theme == "dark" else "light"
        cache_key = f"{name}:{effective_theme}"
        
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        icon = self._load_icon(name, effective_theme)
        self._icon_cache[cache_key] = icon
        
        return icon
    
    def preload(self, icon_names: list[str]) -> None:
        """
        Preload multiple icons for faster access later.
        
        Args:
            icon_names: List of icon names to preload
        """
        theme = self._theme_manager._get_effective_theme()
        
        for name in icon_names:
            cache_key = f"{name}:{theme}"
            if cache_key not in self._icon_cache:
                icon = self._load_icon(name, theme)
                self._icon_cache[cache_key] = icon
                
        self._logger.debug(f"Preloaded {len(icon_names)} icons for theme: {theme}")
    
    def clear_cache(self) -> None:
        """Clear the icon cache. Useful after theme change."""
        self._icon_cache.clear()
        self._logger.debug("Icon cache cleared")
    
    @Slot(str)
    def _on_theme_changed(self, theme: str) -> None:
        """
        Handle theme change from ThemeManager.
        
        Args:
            theme: New theme name ("light" or "dark")
        """
        self._logger.info(f"IconCache: Theme changed to {theme}")
        
        # Clear cache to force reload with new theme
        self.clear_cache()
        
        # Emit signal for widgets to update
        # Note: Individual widgets should connect to theme_manager.theme_changed
        # and call self.update() or get new icons
    
    def register_icon(self, name: str, path: str) -> None:
        """
        Register a custom icon at runtime.
        
        Args:
            name: Icon identifier
            path: Full path to icon file
        """
        if os.path.exists(path):
            icon = QIcon(path)
            theme = self._theme_manager._get_effective_theme()
            cache_key = f"{name}:{theme}"
            self._icon_cache[cache_key] = icon
            self._logger.debug(f"Registered custom icon: {name} -> {path}")
        else:
            self._logger.warning(f"Cannot register icon - file not found: {path}")
    
    @staticmethod
    def get_app_icon() -> QIcon:
        """
        Get the application icon based on current theme.
        
        Returns:
            Application icon
        """
        cache = IconCache()
        return cache.get("icon")
    
    @staticmethod
    def get_tray_icon() -> QIcon:
        """
        Get the system tray icon based on current theme.
        
        Returns:
            Tray icon
        """
        cache = IconCache()
        return cache.get("icon")


# Global instance accessor
_icon_cache_instance: Optional[IconCache] = None


def get_icon_cache() -> IconCache:
    """Get the global IconCache instance."""
    global _icon_cache_instance
    if _icon_cache_instance is None:
        _icon_cache_instance = IconCache()
    return _icon_cache_instance


# Convenience function for getting icons
def get_icon(name: str) -> QIcon:
    """
    Convenience function to get a theme-aware icon.
    
    Args:
        name: Icon name
        
    Returns:
        QIcon with automatic theme selection
    """
    return get_icon_cache().get(name)
