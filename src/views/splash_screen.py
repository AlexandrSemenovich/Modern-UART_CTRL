from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QProgressBar, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QObject, Signal
from PySide6.QtGui import QPixmap, QColor, QFont
import os

from src.utils.translator import tr, translator


class ModernSplashScreen(QWidget):
    """Современный splash экран с прогресс-баром"""
    
    def __init__(self, theme_mode: str = "dark", language: str = "ru"):
        super().__init__()
        self._language = language
        self.theme_mode = theme_mode
        
        # Настройка окна
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Основной layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Фоновая карточка с тенью
        self.background = QLabel(self)
        self.background.setObjectName("SplashCard")
        self.background.setGeometry(10, 10, 380, 480)
        
        # Эффект тени
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.background.setGraphicsEffect(shadow)
        
        # Применяем стиль фона в зависимости от темы
        self._apply_theme()
        
        # Иконка
        self.lbl_icon = QLabel(self.background)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setGeometry(0, 55, 380, 140)
        self.lbl_icon.setObjectName("SplashIcon")
        self._set_icon()
        
        # Заголовок
        self.lbl_title = QLabel(tr("splash_title", "UART Control"), self.background)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setGeometry(0, 200, 380, 40)
        self.lbl_title.setObjectName("SplashTitle")
        self.lbl_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        
        # Подзаголовок
        self.lbl_subtitle = QLabel(tr("splash_subtitle", "Modern COM Port Control"), self.background)
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setGeometry(0, 235, 380, 20)
        self.lbl_subtitle.setObjectName("SplashSubtitle")
        self.lbl_subtitle.setFont(QFont("Arial", 11))
        
        # Статус загрузки
        self.lbl_status = QLabel(tr("loading", "Initializing..."), self.background)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setGeometry(0, 350, 380, 20)
        self.lbl_status.setObjectName("SplashStatus")
        self.lbl_status.setFont(QFont("Arial", 10))
        
        # Прогресс-бар
        self.progress = QProgressBar(self.background)
        self.progress.setGeometry(50, 380, 280, 6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setObjectName("SplashProgress")
        
    
    def _apply_theme(self):
        """Применение темы к splash экрану"""
        if self.theme_mode == "dark":
            # Темная тема
            self.background.setStyleSheet("""
                QLabel#SplashCard {
                    background: rgba(30, 30, 30, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                }
                QLabel#SplashIcon {
                    color: #ffffff;
                }
                QLabel#SplashTitle {
                    color: #ffffff;
                    font-weight: bold;
                }
                QLabel#SplashSubtitle {
                    color: #b0b0b0;
                }
                QLabel#SplashStatus {
                    color: #ffffff;
                }
                QProgressBar#SplashProgress {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 3px;
                    height: 6px;
                }
                QProgressBar#SplashProgress::chunk {
                    background: rgba(100, 150, 255, 0.8);
                    border-radius: 3px;
                }
            """)
        else:
            # Светлая тема
            self.background.setStyleSheet("""
                QLabel#SplashCard {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 15px;
                }
                QLabel#SplashIcon {
                    color: #000000;
                }
                QLabel#SplashTitle {
                    color: #000000;
                    font-weight: bold;
                }
                QLabel#SplashSubtitle {
                    color: #666666;
                }
                QLabel#SplashStatus {
                    color: #000000;
                }
                QProgressBar#SplashProgress {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 3px;
                    height: 6px;
                }
                QProgressBar#SplashProgress::chunk {
                    background: rgba(100, 150, 255, 0.8);
                    border-radius: 3px;
                }
            """)
    
    def _set_icon(self):
        """Установка иконки splash экрана в зависимости от темы"""
        try:
            # Выбираем логотип в зависимости от темы
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
        
        # Если иконки нет, показываем логотип текстом
        self.lbl_icon.setText(tr("splash_logo_text", "UART"))
        self.lbl_icon.setFont(QFont("Arial", 48, QFont.Weight.Bold))
    
    def update_progress(self, value: int, status_text: str = None):
        """Обновление прогресса и статуса"""
        self.progress.setValue(min(100, max(0, value)))

        # Если передан явный статус — показываем его (одна строка)
        if status_text:
            self.lbl_status.setText(status_text)
        else:
            # Автоматический текст в зависимости от прогресса с переводами
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
            # Обновляем одну строку статуса (перезаписываем)
            self.lbl_status.setText(txt)


class SplashController(QObject):
    """Контроллер для управления splash экраном"""
    
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
        """Запуск таймера загрузки"""
        self._elapsed.restart()
        self._timer.start(30)  # Обновление каждые 30ms
    
    def stop(self):
        """Остановка таймера"""
        self._timer.stop()
    
    def _tick(self):
        """Обновление прогресса при каждом тике таймера"""
        self._elapsed_ms = self._elapsed.elapsed()
        ratio = min(1.0, self._elapsed_ms / self._duration_ms)
        progress = int(ratio * 100)
        self._splash.update_progress(progress)
        
        if ratio >= 1.0:
            self._timer.stop()
            self.finished.emit()
    
    def complete(self):
        """Моментальное завершение загрузки"""
        self._timer.stop()
        self._splash.update_progress(100)
        self.finished.emit()
    
    def is_finished(self) -> bool:
        """Проверка, завершена ли загрузка"""
        return self._elapsed_ms >= self._duration_ms
