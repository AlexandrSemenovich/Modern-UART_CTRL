#!/usr/bin/env python3
"""
Structure tests - can run without PySide6.
"""

def test_translations_available():
    """Test translations are properly structured."""
    from src.translations.strings import STRINGS
    assert isinstance(STRINGS, dict)
    assert len(STRINGS) > 0

def test_constants_available():
    """Test constants module is properly structured."""
    from src.styles.constants import Colors, Fonts, Sizes, SerialConfig
    assert hasattr(Colors, 'DARK_BG')
    assert hasattr(Fonts, 'get_monospace_font')
    assert hasattr(Sizes, 'WINDOW_MIN_WIDTH')
    assert hasattr(SerialConfig, 'DEFAULT_BAUD')

def test_main_viewmodel_structure():
    """Test MainViewModel has required methods."""
    from src.viewmodels.main_viewmodel import MainViewModel
    assert hasattr(MainViewModel, 'MAX_CACHE_LINES')
    assert hasattr(MainViewModel, 'format_rx')
    assert hasattr(MainViewModel, 'format_tx')
    assert hasattr(MainViewModel, 'cache_log_line')

def test_serial_worker_structure():
    """Test SerialWorker has required signals."""
    from src.models.serial_worker import SerialWorker
    assert hasattr(SerialWorker, 'rx')
    assert hasattr(SerialWorker, 'status')
    assert hasattr(SerialWorker, 'error')
