import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging with enhanced logger module
from src.utils.logger import setup_logging, get_logger

# Initialize logging based on environment
# Can be overridden with APP_ENV environment variable (development, testing, production, staging)
_env = os.environ.get('APP_ENV', 'development')
setup_logging(env=_env)

logger = get_logger(__name__)
logger.info(f"Starting application in '{_env}' environment")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from src.views.splash_screen import ModernSplashScreen, SplashController
from src.views.main_window import MainWindow
from src.utils.theme_manager import theme_manager
from src.utils.translator import translator, tr

# Global reference to main window
main_window_ref = None

def main():
    global main_window_ref
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Make sure theme is loaded and applied BEFORE splash creation
    # This is important for correct system theme detection
    # On first launch, apply theme forcibly
    theme_manager.apply_theme(force=True)
    
    # Determine current theme and language (after theme application)
    effective_theme = theme_manager._get_effective_theme() if hasattr(theme_manager, '_get_effective_theme') else (
        "dark" if theme_manager.is_dark_theme() else "light"
    )
    language = translator.get_language()
    
    # Create modern splash screen with correct theme
    splash = ModernSplashScreen(theme_mode=effective_theme, language=language)
    splash.show()
    app.processEvents()  # Process events for splash display
    
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
        
        # Make sure theme is applied before creating MainWindow
        theme_manager.apply_theme(force=True)
        
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
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()