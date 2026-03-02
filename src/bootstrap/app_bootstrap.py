"""Application bootstrap sequence for Modern UART Control."""

from __future__ import annotations

import os
import sys
from typing import Iterable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.utils.logger import get_logger, setup_logging
from src.utils.theme_manager import theme_manager
from src.utils.translator import translator, tr
from src.views.main_window import MainWindow
from src.views.splash_screen import ModernSplashScreen, SplashController


class AppBootstrap:
    """Encapsulates application startup logic."""

    def __init__(self, args: Iterable[str] | None = None, env: str | None = None) -> None:
        self._args = list(args or sys.argv)
        self._env = env or os.environ.get("APP_ENV", "development")
        setup_logging(env=self._env)
        self._logger = get_logger(__name__)
        self._app: QApplication | None = None
        self._main_window: MainWindow | None = None
        self._previous_dpi: float | None = None

    def run(self) -> int:
        self._logger.info("Starting application via bootstrap")
        self._app = QApplication(self._args)
        self._app.setStyle("Fusion")
        self._connect_screen_change_handler()
        self._prepare_theme()
        splash, controller = self._create_splash()
        controller.finished.connect(lambda: self._show_main_window(splash))
        self._execute_load_steps(splash, controller)
        return self._app.exec()

    def _connect_screen_change_handler(self) -> None:
        if not self._app:
            return

        def handle_screen_change() -> None:
            if not self._app:
                return
            screen = self._app.primaryScreen()
            if not screen:
                return
            current_dpi = screen.logicalDotsPerInch()
            if self._previous_dpi is not None and current_dpi != self._previous_dpi:
                self._logger.info(
                    "DPI changed from %s to %s, reapplying theme",
                    self._previous_dpi,
                    current_dpi,
                )
                theme_manager.apply_theme(force=True)
            self._previous_dpi = current_dpi

        self._app.screenAdded.connect(handle_screen_change)
        self._app.screenRemoved.connect(handle_screen_change)
        handle_screen_change()

    def _prepare_theme(self) -> None:
        theme_manager.apply_theme(force=True)

    def _create_splash(self) -> tuple[ModernSplashScreen, SplashController]:
        effective_theme = (
            theme_manager._get_effective_theme()  # type: ignore[attr-defined]
            if hasattr(theme_manager, "_get_effective_theme")
            else ("dark" if theme_manager.is_dark_theme() else "light")
        )
        language = translator.get_language()
        splash = ModernSplashScreen(theme_mode=effective_theme, language=language)
        splash.show()
        app = QApplication.instance()
        if app:
            app.processEvents()
        controller = SplashController(splash, duration_ms=3000)
        return splash, controller

    def _show_main_window(self, splash: ModernSplashScreen) -> None:
        splash.close()
        theme_manager.apply_theme(force=True)
        self._main_window = MainWindow()
        self._main_window.show()

    def _execute_load_steps(self, splash: ModernSplashScreen, controller: SplashController) -> None:
        load_steps = [
            (10, tr("loading_initializing", "Initializing application...")),
            (25, tr("loading_theme_manager", "Loading theme manager...")),
            (40, tr("loading_translator", "Loading translator...")),
            (55, tr("loading_models", "Initializing models...")),
            (70, tr("loading_ui", "Building user interface...")),
            (85, tr("loading_styles", "Applying styles...")),
            (95, tr("loading_almost_ready", "Almost ready...")),
        ]

        def execute_step(index: int) -> None:
            if index < len(load_steps):
                progress, message = load_steps[index]
                controller._elapsed_ms = int(progress / 100.0 * 3000)
                splash.update_progress(progress, message)
                app = QApplication.instance()
                if app:
                    app.processEvents()
                QTimer.singleShot(100, lambda i=index + 1: execute_step(i))
            else:
                controller.start()

        splash.update_progress(0, tr("loading", "Initializing..."))
        app = QApplication.instance()
        if app:
            app.processEvents()
        execute_step(0)


def run_bootstrap(env: str | None = None) -> int:
    bootstrap = AppBootstrap(env=env)
    return bootstrap.run()
