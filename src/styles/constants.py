"""
Unified style constants for the entire application.
Provides colors, fonts, sizes, and spacing.
"""

from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase
import logging

from src.utils.config_loader import config_loader

# ==================== Colors ====================
class Colors:
    """Color palette for the application."""

    def __init__(self) -> None:
        self._cache = {}

    def get_theme_colors(self, theme: str):
        if theme not in self._cache:
            self._cache[theme] = config_loader.get_colors(theme)
        return self._cache[theme]
    
    # Search highlight colors (RGBA format for QColor)
    # All matches - gray/neutral highlight
    SEARCH_MATCH_COLOR = (128, 128, 128, 80)   # Gray, semi-transparent
    # Current selected match - orange/bright highlight
    SEARCH_CURRENT_COLOR = (255, 165, 0, 180)   # Orange, more opaque


# ==================== Fonts ====================
class Fonts:
    """Font definitions with lazy config access."""

    _config = config_loader.get_fonts()
    
    # Monospace font families in order of preference
    MONOSPACE_FAMILIES = [
        "Cascadia Code",
        "Consolas",
        "Fira Code",
        "Courier New",
        "monospace",
    ]

    @classmethod
    def get_monospace_font(cls) -> QFont:
        """Get monospace font with fallback for unavailable fonts."""
        # Try each font family in order of preference
        available_family = cls._find_available_font(cls.MONOSPACE_FAMILIES)
        
        font = QFont()
        font.setFamily(available_family)
        font.setPointSize(cls._config.monospace_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
    
    @classmethod
    def _find_available_font(cls, families: list[str]) -> str:
        """Find the first available font family from the list."""
        available_families = QFontDatabase.families()
        
        for family in families:
            if family in available_families:
                return family
        
        # Ultimate fallback - Qt will use system default
        return "monospace"

    @classmethod
    def get_default_font(cls) -> QFont:
        font = QFont()
        font.setFamily(cls._config.default_family)
        font.setPointSize(cls._config.default_size)
        return font

    @classmethod
    def get_button_font(cls) -> QFont:
        font = QFont()
        font.setFamily(cls._config.default_family)
        font.setPointSize(cls._config.button_size)
        return font

    @classmethod
    def get_title_font(cls) -> QFont:
        font = QFont()
        font.setFamily(cls._config.default_family)
        font.setPointSize(cls._config.title_size)
        font.setBold(True)
        return font
    
    @classmethod
    def get_caption_font(cls) -> QFont:
        """Get small/caption text font."""
        font = QFont()
        font.setFamily(cls._config.default_family)
        font.setPointSize(cls._config.caption_size)
        return font

    # ==================== Typography Scale ====================
    # Getters for QSS to use directly (returns pt values)
    @classmethod
    def get_default_size_pt(cls) -> int:
        """Get default body text size in points."""
        return cls._config.default_size
    
    @classmethod
    def get_title_size_pt(cls) -> int:
        """Get title text size in points."""
        return cls._config.title_size
    
    @classmethod
    def get_button_size_pt(cls) -> int:
        """Get button text size in points."""
        return cls._config.button_size
    
    @classmethod
    def get_caption_size_pt(cls) -> int:
        """Get caption/small text size in points."""
        return cls._config.caption_size
    
    @classmethod
    def get_monospace_size_pt(cls) -> int:
        """Get monospace (console) text size in points."""
        return cls._config.monospace_size


# ==================== Sizes ====================
class Sizes:
    """Size definitions accessible as class attributes."""

    _cfg = config_loader.get_sizes()
    WINDOW_MIN_WIDTH = _cfg.window_min_width
    WINDOW_MIN_HEIGHT = _cfg.window_min_height
    WINDOW_DEFAULT_WIDTH = _cfg.window_default_width
    WINDOW_DEFAULT_HEIGHT = _cfg.window_default_height
    LEFT_PANEL_MIN_WIDTH = _cfg.left_panel_min_width
    LEFT_PANEL_MAX_WIDTH = _cfg.left_panel_max_width
    CENTER_PANEL_MIN_WIDTH = _cfg.center_panel_min_width
    RIGHT_PANEL_MIN_WIDTH = _cfg.right_panel_min_width
    RIGHT_PANEL_MAX_WIDTH = _cfg.right_panel_max_width
    LAYOUT_SPACING = _cfg.layout_spacing
    LAYOUT_MARGIN = _cfg.layout_margin
    CARD_MARGIN = 8  # Inner margin for card-style widgets (left, right, top, bottom)
    TOOLBAR_SPACING = _cfg.toolbar_spacing
    TOOLBAR_MARGIN = _cfg.toolbar_margin
    BUTTON_MIN_HEIGHT = _cfg.button_min_height
    BUTTON_MAX_WIDTH = _cfg.button_max_width
    BUTTON_CLEAR_MAX_WIDTH = _cfg.button_clear_max_width
    BUTTON_SAVE_MAX_WIDTH = _cfg.button_save_max_width
    INPUT_MIN_HEIGHT = _cfg.input_min_height
    SEARCH_FIELD_MAX_WIDTH = _cfg.search_field_max_width


# ==================== Timing ====================
class Timing:
    """Timing constants for animations and delays."""
    
    # Connection animation
    CONNECT_ANIMATION_INTERVAL_MS = 100
    CONNECT_ANIMATION_FRAMES = 4
    
    # LED pulse animation for connecting state
    LED_PULSE_INTERVAL_MS = 300
    LED_PULSE_MIN_OPACITY = 0.4
    LED_PULSE_MAX_OPACITY = 1.0


# ==================== Flash Animation ====================
class FlashAnimation:
    """
    Constants for TX flash animation (visual feedback on command send).
    Grouped by theme for easy customization.
    """
    
    # Animation duration
    FLASH_DURATION_MS = 200
    
    # Dark theme colors - WCAG AA compliant (4.5:1 minimum)
    # Primary text: #e5e7eb on #020617 = 14:1 contrast
    # Secondary text: #9ca3af on #020617 = 4.5:1 contrast
    DARK_FLASH_COLOR = "#22c55e"          # Green-500
    DARK_FLASH_BG = "rgba(34, 197, 94, 0.15)"  # Green with 15% opacity
    DARK_TEXT_COLOR = "#e5e7eb"           # Gray-200 - high contrast
    
    # Light theme colors
    LIGHT_FLASH_COLOR = "#0d9488"          # Teal-600
    LIGHT_FLASH_BG = "rgba(13, 148, 136, 0.1)"  # Teal with 10% opacity
    LIGHT_TEXT_COLOR = "#0f172a"           # Slate-900 - high contrast
    
    # Border settings
    BORDER_WIDTH = "1px"
    BORDER_RADIUS = "4px"
    
    # Convenience methods
    @classmethod
    def get_flash_colors(cls, is_dark: bool) -> dict:
        """
        Get flash colors based on theme.
        
        Args:
            is_dark: True for dark theme, False for light theme
            
        Returns:
            dict with keys: flash_color, flash_bg, text_color
        """
        if is_dark:
            return {
                "flash_color": cls.DARK_FLASH_COLOR,
                "flash_bg": cls.DARK_FLASH_BG,
                "text_color": cls.DARK_TEXT_COLOR,
            }
        else:
            return {
                "flash_color": cls.LIGHT_FLASH_COLOR,
                "flash_bg": cls.LIGHT_FLASH_BG,
                "text_color": cls.LIGHT_TEXT_COLOR,
            }
    
    @classmethod
    def get_button_flash_style(cls, is_dark: bool) -> str:
        """Get QSS style string for button flash animation."""
        colors = cls.get_flash_colors(is_dark)
        return f"""
            QPushButton {{
                border: {cls.BORDER_WIDTH} solid {colors["flash_color"]};
                background-color: {colors["flash_bg"]};
                color: {colors["text_color"]};
                border-radius: {cls.BORDER_RADIUS};
            }}
        """
    
    @classmethod
    def get_input_flash_style(cls, is_dark: bool) -> str:
        """Get QSS style string for input field flash animation."""
        colors = cls.get_flash_colors(is_dark)
        return f"""
            QLineEdit {{
                border: {cls.BORDER_WIDTH} solid {colors["flash_color"]};
                border-radius: {cls.BORDER_RADIUS};
                padding: 4px 8px;
                background: {colors["flash_bg"]};
                color: palette(text);
            }}
        """


# ==================== Configuration ====================
class SerialConfig:
    """Default serial port configuration."""

    _cfg = config_loader.get_serial_config()
    DEFAULT_BAUD = int(_cfg.get("default_baud", 115200))
    BAUD_RATES = [int(b) for b in _cfg.get("baud_rates", "1200,2400,4800,9600,19200,38400,57600,115200").split(",")]
    PORT_LABEL_1 = _cfg.get("port_label_1", "CPU1")
    PORT_LABEL_2 = _cfg.get("port_label_2", "CPU2")
    PORT_LABEL_TLM = _cfg.get("port_label_3", "TLM")
    DEFAULT_PORTS = _cfg.get("default_ports", "COM1,COM2,COM3,COM4,COM5").split(",")


class SerialPorts:
    """Common serial port definitions and restrictions."""

    _cfg = config_loader.get_ports_config()
    # Reserved system ports that must not be used by the application
    SYSTEM_PORTS = set(p.strip().upper() for p in _cfg.get("system_ports", "COM1,COM2").split(","))


class ConsoleLimits:
    """Constraints for console widgets to prevent memory bloat."""
    _cfg = config_loader.get_console_config()

    # Maximum HTML length for a single log chunk
    MAX_HTML_LENGTH = _cfg.max_html_length
    # Maximum number of lines in QTextEdit document
    MAX_DOCUMENT_LINES = _cfg.max_document_lines
    # Chunk size when trimming old lines
    TRIM_CHUNK_SIZE = _cfg.trim_chunk_size
    # Maximum number of cached log lines per port
    MAX_CACHE_LINES = _cfg.max_cache_lines


# ==================== Charset Detection ====================
class CharsetConfig:
    """Charset detection configuration for serial data."""

    # Common charsets for serial data detection
    COMMON_CHARSETS = [
        'utf-8',
        'latin-1',
        'cp1251',
        'koi8-r',
        'iso-8859-1',
        'ascii',
    ]

    # Auto-detect charset patterns (common serial data prefixes)
    CHARSET_PATTERNS = {
        b'\xfe\xff': 'utf-16-be',
        b'\xff\xfe': 'utf-16-le',
        b'\xef\xbb\xbf': 'utf-8',
    }


# ==================== Command Validation ====================
import string

class CommandConfig:
    """Command validation configuration for serial port communication."""

    # Maximum command length in characters
    MAX_COMMAND_LENGTH = 1024
    
    # Valid characters: printable ASCII + CR + LF
    VALID_CHARS = set(string.printable + "\r\n")


# ==================== Logging ====================
class LoggingConfig:
    """Logging configuration constants."""
    
    # Log directory relative to project root
    LOG_DIR = Path('logs')
    
    # Maximum size of each log file (10 MB)
    MAX_BYTES = 10 * 1024 * 1024
    
    # Number of backup files to keep
    BACKUP_COUNT = 5
    
    # Default log format
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Log levels per environment
    ENV_LEVELS = {
        'development': logging.DEBUG,
        'testing': logging.DEBUG,
        'production': logging.INFO,
        'staging': logging.WARNING,
    }
    
    # Default environment
    DEFAULT_ENV = 'development'
    
    # Environment variable name
    ENV_VAR = 'APP_ENV'


# ==================== Toast Notifications ====================
class ToastConfig:
    """Toast notification configuration."""
    
    _cfg = config_loader.get_toast_config()
    
    # Toast dimensions
    TOAST_MIN_WIDTH = _cfg.toast_min_width
    TOAST_MAX_WIDTH = _cfg.toast_max_width
    TOAST_MARGINS = _cfg.toast_margins
    TOAST_CORNER_RADIUS = _cfg.toast_corner_radius
    
    # Toast sizing
    TOAST_ICON_SIZE = _cfg.toast_icon_size
    TOAST_CLOSE_BUTTON_SIZE = _cfg.toast_close_button_size
    
    # Timing
    TOAST_DURATION_MS = _cfg.toast_duration_ms
    TOAST_SPACING = _cfg.toast_spacing
