import sys
import os
import logging

# Добавляем родительскую директорию в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging with proper format
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.views.splash_screen import ModernSplashScreen, SplashController
from src.views.main_window import MainWindow
from src.utils.theme_manager import theme_manager
from src.utils.translator import translator, tr

# Global reference to main window
main_window_ref = None

def main():
    global main_window_ref
    
    # Создание приложения
    app = QApplication(sys.argv)
    
    # Установка стиля приложения
    app.setStyle('Fusion')
    
    # Определяем текущую тему и язык
    is_dark = theme_manager.is_dark_theme()
    theme_mode = "dark" if is_dark else "light"
    language = translator.get_language()
    
    # Создание modern splash screen
    splash = ModernSplashScreen(theme_mode=theme_mode, language=language)
    splash.show()
    app.processEvents()  # Обработка событий для отображения splash
    
    # Create splash controller
    controller = SplashController(splash, duration_ms=3000)
    
    # Define load steps
    load_steps = [
        (10, tr("loading_initializing", "Initializing application...")),
        (25, tr("loading_theme_manager", "Loading theme manager...")),
        (40, tr("loading_translator", "Loading translator...")),
        (55, tr("loading_models", "Initializing models...")),
        (70, tr("loading_ui", "Building user interface...")),
        (85, tr("loading_styles", "Applying styles...")),
        (95, tr("loading_almost_ready", "Almost ready...")),
    ]
    
    # Handler for splash finished
    def on_splash_finished():
        global main_window_ref
        splash.close()
        
        main_window_ref = MainWindow()
        main_window_ref.show()
    
    controller.finished.connect(on_splash_finished)
    
    # Update progress for each step
    def execute_load_step(index: int):
        """Execute a single load step and schedule the next."""
        if index < len(load_steps):
            progress, message = load_steps[index]
            controller._elapsed_ms = int(progress / 100.0 * 3000)
            splash.update_progress(progress, message)
            app.processEvents()
            # Schedule next step
            QTimer.singleShot(100, lambda i=index+1: execute_load_step(i))
        else:
            # All steps complete, start animation
            controller.start()
    
    # Start loading
    splash.update_progress(0, tr("loading", "Initializing..."))
    app.processEvents()
    
    # Begin step-by-step loading
    execute_load_step(0)
    
    # Запуск приложения
    sys.exit(app.exec())

if __name__ == "__main__":
    main()