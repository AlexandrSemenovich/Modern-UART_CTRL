from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QProgressBar, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QObject, Signal
from PySide6.QtGui import QPixmap, QColor
import os

from src.utils.translator import tr, translator
from src.utils.theme_manager import theme_manager
from src.styles.constants import Fonts


class ModernSplashScreen(QWidget):
    """Modern splash screen with progress bar"""
    
    def __init__(self, theme_mode: str = "dark", language: str = "ru"):
        super().__init__()
        self._language = language
        self.theme_mode = theme_mode
        
        # Window setup
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Background card with shadow
        self.background = QLabel(self)
        self.background.setObjectName("SplashCard")
        self.background.setGeometry(10, 10, 380, 480)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.background.setGraphicsEffect(shadow)
        
        # Icon
        self.lbl_icon = QLabel(self.background)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setGeometry(0, 55, 380, 140)
        self.lbl_icon.setObjectName("SplashIcon")
        self._set_icon()
        
        # Title
        self.lbl_title = QLabel(tr("splash_title", "UART Control"), self.background)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setGeometry(0, 200, 380, 40)
        self.lbl_title.setObjectName("SplashTitle")
        title_font = Fonts.get_title_font()
        title_font.setPointSize(24)
        self.lbl_title.setFont(title_font)
        
        # Subtitle
        self.lbl_subtitle = QLabel(tr("splash_subtitle", "Modern COM Port Control"), self.background)
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setGeometry(0, 235, 380, 20)
        self.lbl_subtitle.setObjectName("SplashSubtitle")
        subtitle_font = Fonts.get_default_font()
        subtitle_font.setPointSize(11)
        self.lbl_subtitle.setFont(subtitle_font)
        
        # Loading status
        self.lbl_status = QLabel(tr("loading", "Initializing..."), self.background)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setGeometry(0, 350, 380, 20)
        self.lbl_status.setObjectName("SplashStatus")
        self.lbl_status.setFont(Fonts.get_default_font())
        
        # Progress bar
        self.progress = QProgressBar(self.background)
        self.progress.setGeometry(50, 380, 280, 6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setObjectName("SplashProgress")

        # Apply background style based on theme (after all widgets are created)
        self._apply_theme()
        
    
    def _apply_theme(self):
        """Apply theme to splash screen - uses shared style system"""
        # Use theme_mode passed when creating splash screen
        # This ensures splash screen uses the same theme as the application
        effective_theme = self.theme_mode
        
        # Set themeClass for QSS application
        self.setProperty("themeClass", effective_theme)
        self.background.setProperty("themeClass", effective_theme)
        self.lbl_title.setProperty("themeClass", effective_theme)
        self.lbl_subtitle.setProperty("themeClass", effective_theme)
        self.lbl_status.setProperty("themeClass", effective_theme)
        self.progress.setProperty("themeClass", effective_theme)
    
    def _set_icon(self):
        """Set splash screen icon based on theme"""
        try:
            # Select logo based on theme
            logo_name = "logo_white.png" if self.theme_mode == "dark" else "logo_black.png"
            icon_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "assets", "images", logo_name
            )
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        140, 140,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.lbl_icon.setPixmap(pixmap)
                    return
        except Exception:
            pass
        
        # If no icon, show logo as text
        self.lbl_icon.setText(tr("splash_logo_text", "UART"))
        logo_font = Fonts.get_title_font()
        logo_font.setPointSize(48)
        self.lbl_icon.setFont(logo_font)
    
    def update_progress(self, value: int, status_text: str = None):
        """Update progress and status"""
        self.progress.setValue(min(100, max(0, value)))

        # If explicit status is passed - show it (one line)
        if status_text:
            self.lbl_status.setText(status_text)
        else:
            # Automatic text based on progress with translations
            if value < 20:
                txt = tr("loading_initializing", "Initializing application...")
            elif value < 40:
                txt = tr("loading_theme_manager", "Loading theme manager...")
            elif value < 60:
                txt = tr("loading_translator", "Loading translator...")
            elif value < 80:
                txt = tr("loading_models", "Initializing models...")
            elif value < 95:
                txt = tr("loading_ui", "Building user interface...")
            elif value < 100:
                txt = tr("loading_styles", "Applying styles...")
            else:
                txt = tr("ready", "Ready!")
            # Update single status line (overwrite)
            self.lbl_status.setText(txt)


class SplashController(QObject):
    """Controller for splash screen management"""
    
    finished = Signal()
    
    def __init__(self, splash: ModernSplashScreen, duration_ms: int = 3000):
        super().__init__()
        self._splash = splash
        self._duration_ms = max(1000, duration_ms)
        self._elapsed_ms = 0
        self._elapsed = QElapsedTimer()
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
    
    def start(self):
        """Start loading timer"""
        self._elapsed.restart()
        self._timer.start(30)  # Update every 30ms
    
    def stop(self):
        """Stop timer"""
        self._timer.stop()
    
    def _tick(self):
        """Update progress on each timer tick"""
        self._elapsed_ms = self._elapsed.elapsed()
        ratio = min(1.0, self._elapsed_ms / self._duration_ms)
        progress = int(ratio * 100)
        self._splash.update_progress(progress)
        
        if ratio >= 1.0:
            self._timer.stop()
            self.finished.emit()
    
    def complete(self):
        """Instant completion of loading"""
        self._timer.stop()
        self._splash.update_progress(100)
        self.finished.emit()
    
    def is_finished(self) -> bool:
        """Check if loading is complete"""
        return self._elapsed_ms >= self._duration_ms
