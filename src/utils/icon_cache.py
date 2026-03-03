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

import hashlib
import json
import logging
import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QIconEngine, QImage, QScreen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QWidget

from src.utils.theme_manager import ThemeManager
from src.utils.paths import get_config_dir, get_root_dir


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
    
    _instance: 'IconCache | None' = None
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
        self._icon_cache: dict[str, dict[str, QIcon]] = {}
        self._resolved_paths: dict[str, dict[str, str]] = {}
        self._theme_suffix_cache: dict[str, str] = {}  # theme -> suffix mapping
        self._icon_manifest: dict[str, str] = {}
        self._manifest_path = get_config_dir() / "assets" / "icon_manifest.json"

        # Get base icons directory
        self._load_manifest()
        self._base_icons_dir = self._get_icons_directory()
        self._logger.info("IconCache base dir: %s", self._base_icons_dir)
        
        # Connect to theme manager
        self._theme_manager = ThemeManager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        self._logger.info(f"IconCache initialized. Base directory: {self._base_icons_dir}")
    
    def _mirror_icons_directory(self, source: Path) -> str | None:
        version_token = str(int(os.path.getmtime(source)))
        target_root = get_config_dir() / "assets"
        versioned_dir = target_root / "icons" / version_token
        checksum = self._calculate_directory_checksum(source)
        manifest_entry = self._icon_manifest.get(checksum)
        if manifest_entry and Path(manifest_entry).exists():
            return manifest_entry
        try:
            versioned_dir = target_root / "icons" / f"{version_token}_{checksum[:8]}"
            if versioned_dir.exists():
                directory_path = str(versioned_dir)
            else:
                versioned_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, versioned_dir, dirs_exist_ok=True)
                directory_path = str(versioned_dir)
            self._icon_manifest[checksum] = directory_path
            self._save_manifest()
            self._cleanup_old_icons(versioned_dir.parent, keep=2)
            return directory_path
        except OSError as exc:
            self._logger.warning("Failed to mirror icons from %s to %s: %s", source, versioned_dir, exc)
            return None

    def _cleanup_old_icons(self, base_dir: Path, keep: int = 2) -> None:
        try:
            versions = sorted(p for p in base_dir.iterdir() if p.is_dir())
            for obsolete in versions[:-keep]:
                shutil.rmtree(obsolete, ignore_errors=True)
                self._remove_manifest_entry(str(obsolete))
        except OSError:
            pass
        self._cleanup_manifest_references()

    def _cleanup_manifest_references(self) -> None:
        changed = False
        for checksum, path in list(self._icon_manifest.items()):
            if not Path(path).exists():
                self._icon_manifest.pop(checksum, None)
                changed = True
        if changed:
            self._save_manifest()

    def _remove_manifest_entry(self, path: str) -> None:
        removed = False
        for checksum, stored_path in list(self._icon_manifest.items()):
            if stored_path == path:
                self._icon_manifest.pop(checksum, None)
                removed = True
        if removed:
            self._save_manifest()

    def _get_icons_directory(self) -> str:
        """Get the base icons directory path."""
        root_dir = get_root_dir()
        exe_dir = Path(sys.executable).resolve().parent
        frozen = bool(getattr(sys, "frozen", False))

        search_paths = [
            root_dir / "assets" / "icons",
            exe_dir / "assets" / "icons",
            exe_dir / "_internal" / "assets" / "icons",
        ]

        if hasattr(sys, "_MEIPASS"):
            meipass = Path(getattr(sys, "_MEIPASS"))
            search_paths.extend([
                meipass / "assets" / "icons",
                meipass / "_internal" / "assets" / "icons",
            ])

        for candidate in search_paths:
            if candidate.exists():
                if frozen:
                    mirrored = self._mirror_icons_directory(candidate)
                    if mirrored:
                        return mirrored
                else:
                    return str(candidate)

        fallback = search_paths[0]
        self._logger.warning(f"Icons directory not found. Using fallback: {fallback}")
        return str(fallback)

    def _calculate_directory_checksum(self, source: Path) -> str:
        digest = hashlib.sha256()
        try:
            for root, _dirs, files in os.walk(source):
                for name in sorted(files):
                    file_path = Path(root) / name
                    digest.update(str(file_path.relative_to(source)).encode("utf-8"))
                    try:
                        with open(file_path, "rb") as fh:
                            for chunk in iter(lambda: fh.read(8192), b""):
                                digest.update(chunk)
                    except OSError:
                        continue
        except OSError:
            return ""
        return digest.hexdigest()

    def _load_manifest(self) -> None:
        if self._manifest_path.exists():
            try:
                self._icon_manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._icon_manifest = {}
        else:
            self._icon_manifest = {}

    def _save_manifest(self) -> None:
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._manifest_path.write_text(json.dumps(self._icon_manifest, indent=2), encoding="utf-8")
        except OSError:
            pass
    
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
    
    def _resolve_icon_path(self, name: str, theme: str) -> str | None:
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
        # Use cache if available
        cached = self._resolved_paths.get(name, {}).get(theme)
        if cached:
            return cached

        theme_folder = theme  # "light" or "dark"
        extensions = [".svg", ".ico", ".png", ".jpg"]

        for ext in extensions:
            folder_path = os.path.join(self._base_icons_dir, theme_folder, f"{name}{ext}")
            if os.path.exists(folder_path):
                self._resolved_paths.setdefault(name, {})[theme] = folder_path
                return folder_path
        
        # ==== Check fa/ subdirectory with theme suffixes (legacy format) ====
        theme_suffix = self._get_theme_suffix(theme)
        
        # Try theme-specific icon in fa/
        for ext in [".svg"]:
            themed_name = f"{name}{theme_suffix}{ext}"
            fa_path = os.path.join(self._base_icons_dir, "fa", themed_name)
            if os.path.exists(fa_path):
                self._resolved_paths.setdefault(name, {})[theme] = fa_path
                return fa_path
        
        # Fallback to neutral in fa/
        for ext in [".svg"]:
            neutral_name = f"{name}{ext}"
            fa_path = os.path.join(self._base_icons_dir, "fa", neutral_name)
            if os.path.exists(fa_path):
                self._resolved_paths.setdefault(name, {})[theme] = fa_path
                return fa_path
        
        # ==== Special case: icon in root directory (legacy ICO files) ====
        if name == "icon":
            if theme == "dark":
                ico_name = "icon_black.ico"
            else:
                ico_name = "icon_white.ico"
            root_path = os.path.join(self._base_icons_dir, ico_name)
            if os.path.exists(root_path):
                self._resolved_paths.setdefault(name, {})[theme] = root_path
                return root_path

        self._logger.warning(f"Icon not found: {name} (theme: {theme})")
        return None
    
    def _render_svg_icon(self, path: str) -> QIcon:
        renderer = QSvgRenderer(path)
        if not renderer.isValid():
            self._logger.warning("SVG renderer invalid for %s", path)
            return QIcon()

        default_size = renderer.defaultSize()
        if not default_size.isValid() or default_size.width() == 0 or default_size.height() == 0:
            default_size = QSize(64, 64)

        pixmap = QPixmap(default_size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        icon = QIcon(pixmap)
        icon.addPixmap(pixmap)
        return icon

    def _create_icon(self, path: str) -> QIcon:
        suffix = Path(path).suffix.lower()
        if suffix == ".svg":
            return self._render_svg_icon(path)

        icon = QIcon(path)
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            size = pixmap.size()
            self._logger.debug(
                "IconCache: pixmap loaded for %s with size %dx%d",
                path,
                size.width(),
                size.height(),
            )
        else:
            self._logger.warning("IconCache: pixmap could not be loaded for %s", path)

        if icon.isNull() and not pixmap.isNull():
            icon = QIcon(pixmap)
            self._logger.debug("IconCache: created icon from pixmap for %s", path)
        return icon

    def _load_icon(self, name: str, theme: str) -> QIcon:
        icon_path = self._resolve_icon_path(name, theme)
        if icon_path is None:
            return QIcon()

        icon = self._create_icon(icon_path)

        if icon.isNull():
            self._logger.warning("Failed to create icon from %s", icon_path)

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
        
        themed_cache = self._icon_cache.setdefault(name, {})
        if theme in themed_cache:
            return themed_cache[theme]

        icon = self._load_icon(name, theme)
        if icon.isNull():
            self._logger.warning(
                "Icon '%s' is null even after loading from %s (themes: %s)",
                name,
                self._base_icons_dir,
                os.listdir(self._base_icons_dir),
            )
        themed_cache[theme] = icon

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
        themed_cache = self._icon_cache.setdefault(name, {})
        if effective_theme in themed_cache:
            return themed_cache[effective_theme]

        icon = self._load_icon(name, effective_theme)
        themed_cache[effective_theme] = icon

        return icon
    
    def preload(self, icon_names: list[str]) -> None:
        """
        Preload multiple icons for faster access later.
        
        Args:
            icon_names: List of icon names to preload
        """
        theme = self._theme_manager._get_effective_theme()
        
        for name in icon_names:
            themed_cache = self._icon_cache.setdefault(name, {})
            if theme not in themed_cache:
                icon = self._load_icon(name, theme)
                themed_cache[theme] = icon
                
        self._logger.debug(f"Preloaded {len(icon_names)} icons for theme: {theme}")
    
    def clear_cache(self) -> None:
        """Clear the icon cache. Useful after theme change."""
        self._icon_cache.clear()
        self._resolved_paths.clear()
        self._logger.debug("Icon cache cleared")
        self._release_cached_widgets()

    def _release_cached_widgets(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()
        except Exception:
            pass
    
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
            themed_cache = self._icon_cache.setdefault(name, {})
            themed_cache[theme] = icon
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
_icon_cache_instance: IconCache | None = None


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
