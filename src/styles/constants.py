"""
Unified style constants for the entire application.
Provides colors, fonts, sizes, and spacing.
"""

from PySide6.QtGui import QFont

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
    
    # Common color constants for backwards compatibility
    DARK_BG = "#1e1e1e"
    LIGHT_BG = "#f5f5f5"
    DARK_TEXT = "#ffffff"
    LIGHT_TEXT = "#000000"


# ==================== Fonts ====================
class Fonts:
    """Font definitions with lazy config access."""

    _config = config_loader.get_fonts()

    @classmethod
    def get_monospace_font(cls) -> QFont:
        font = QFont()
        font.setFamily(cls._config.monospace_family)
        font.setPointSize(cls._config.monospace_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font

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
    
    LED_FLASH_DURATION_MS = 150
    SERIAL_READ_INTERVAL_MS = 20


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
