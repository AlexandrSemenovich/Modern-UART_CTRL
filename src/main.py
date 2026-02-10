import sys
import os
import time

# Добавляем родительскую директорию в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
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
    
    # Создание контроллера splash экрана
    controller = SplashController(splash, duration_ms=3000)
    
    # Переменные для отслеживания этапов загрузки
    load_steps = [
        (10, tr("loading_initializing", "Initializing application...")),
        (25, tr("loading_theme_manager", "Loading theme manager...")),
        (40, tr("loading_translator", "Loading translator...")),
        (55, tr("loading_models", "Initializing models...")),
        (70, tr("loading_ui", "Building user interface...")),
        (85, tr("loading_styles", "Applying styles...")),
        (95, tr("loading_almost_ready", "Almost ready...")),
    ]
    
    # Обработчик завершения загрузки
    def on_splash_finished():
        global main_window_ref
        splash.close()
        
        # Создание главного окна
        main_window_ref = MainWindow()
        main_window_ref.show()
    
    controller.finished.connect(on_splash_finished)
    
    # Запуск с информативными сообщениями
    splash.update_progress(0, tr("loading", "Initializing..."))
    app.processEvents()
    
    for progress, message in load_steps:
        controller._elapsed_ms = int(progress / 100.0 * 3000)
        splash.update_progress(progress, message)
        app.processEvents()
        time.sleep(0.1)
    
    controller.start()
    
    # Запуск приложения
    sys.exit(app.exec())

if __name__ == "__main__":
    main()