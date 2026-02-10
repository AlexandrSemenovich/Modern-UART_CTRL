"""
Unified style constants for the entire application.
Provides colors, fonts, sizes, and spacing.
"""

from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

# ==================== Colors ====================
class Colors:
    """Color palette for the application."""
    
    # Log types - colors for console output
    RX_COLOR = "#c7f0c7"      # Green for RX messages
    TX_COLOR = "#fff7d6"      # Yellow for TX messages
    SYS_COLOR = "lightgray"   # Gray for system messages
    
    # UI elements
    TIMESTAMP_COLOR = "gray"   # Timestamp in logs
    SOURCE_LABEL_COLOR = "green"  # RX label
    SOURCE_LABEL_TX_COLOR = "#ffdd57"  # TX label
    SOURCE_LABEL_SYS_COLOR = "lightgray"  # SYS label
    
    # Status and indicators
    LED_OFF_COLOR = "#333333"  # LED off state
    LED_RX_COLOR = "#00ff00"   # LED RX indicator
    LED_TX_COLOR = "#ffcc33"   # LED TX indicator
    
    # Backgrounds (dark theme)
    DARK_BG = "#1e1e1e"
    DARK_FG = "#ffffff"
    
    # Backgrounds (light theme)
    LIGHT_BG = "#ffffff"
    LIGHT_FG = "#000000"


# ==================== Fonts ====================
class Fonts:
    """Font definitions for the application."""
    
    @staticmethod
    def get_monospace_font(size: int = 9) -> QFont:
        """Get monospace font for console/log display."""
        font = QFont()
        font.setFamily("Courier New")
        font.setPointSize(size)
        font.setStyleStrategy(QFont.PreferAntialias)
        return font
    
    @staticmethod
    def get_default_font(size: int = 10) -> QFont:
        """Get default font for UI elements."""
        font = QFont()
        font.setPointSize(size)
        return font
    
    @staticmethod
    def get_button_font(size: int = 10, bold: bool = False) -> QFont:
        """Get font for buttons."""
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font
    
    @staticmethod
    def get_title_font(size: int = 14, bold: bool = True) -> QFont:
        """Get font for titles."""
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font


# ==================== Sizes ====================
class Sizes:
    """Size definitions for the application."""
    
    # Window
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    WINDOW_DEFAULT_WIDTH = 1200
    WINDOW_DEFAULT_HEIGHT = 800
    
    # Panels
    LEFT_PANEL_MIN_WIDTH = 320
    LEFT_PANEL_MAX_WIDTH = 380
    CENTER_PANEL_MIN_WIDTH = 400
    RIGHT_PANEL_MIN_WIDTH = 200
    RIGHT_PANEL_MAX_WIDTH = 350
    
    # Buttons
    BUTTON_MIN_HEIGHT = 32
    BUTTON_MAX_WIDTH = 80
    BUTTON_CLEAR_MAX_WIDTH = 80
    BUTTON_SAVE_MAX_WIDTH = 80
    
    # Input fields
    INPUT_MIN_HEIGHT = 32
    SEARCH_FIELD_MAX_WIDTH = 200
    
    # Group boxes
    GROUP_BOX_MIN_HEIGHT = 80
    
    # Text areas
    LOG_MIN_HEIGHT = 60
    STATUS_MIN_HEIGHT = 100
    TLM_LOG_MIN_HEIGHT = 100
    
    # Spacing and margins
    LAYOUT_SPACING = 5
    LAYOUT_MARGIN = 5
    TOOLBAR_SPACING = 5
    TOOLBAR_MARGIN = 0
    
    # LED indicator
    LED_SIZE = 16
    LED_BORDER_RADIUS = 8


# ==================== Timing ====================
class Timing:
    """Timing constants for animations and delays."""
    
    LED_FLASH_DURATION_MS = 150
    SERIAL_READ_INTERVAL_MS = 20


# ==================== Configuration ====================
class SerialConfig:
    """Default serial port configuration."""
    
    DEFAULT_BAUD = 115200
    BAUD_RATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    
    # Port labels
    PORT_LABEL_1 = "CPU1"
    PORT_LABEL_2 = "CPU2"
    PORT_LABEL_TLM = "TLM"
    
    # Default ports (if no real ports available)
    DEFAULT_PORTS = ["COM1", "COM2", "COM3", "COM4", "COM5"]
