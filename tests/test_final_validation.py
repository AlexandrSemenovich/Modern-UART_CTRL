"""
Final Validation Script - Tests for core functionality.
"""

def test_imports():
    """Test that core modules can be imported."""
    from src.styles.constants import Colors, Fonts, Sizes
    assert Colors is not None
    assert Fonts is not None
    assert Sizes is not None

def test_serial_worker_import():
    """Test that serial_worker module structure is correct."""
    from src.models.serial_worker import SerialWorker
    assert hasattr(SerialWorker, 'rx')
    assert hasattr(SerialWorker, 'status')
    assert hasattr(SerialWorker, 'error')

def test_main_viewmodel_import():
    """Test that main_viewmodel has required attributes."""
    from src.viewmodels.main_viewmodel import MainViewModel
    assert hasattr(MainViewModel, 'MAX_CACHE_LINES')
    assert hasattr(MainViewModel, 'format_rx')
    assert hasattr(MainViewModel, 'format_tx')
    assert hasattr(MainViewModel, 'format_system')

def test_translations():
    """Test translations are loaded."""
    from src.translations.strings import STRINGS
    assert isinstance(STRINGS, dict)
    assert len(STRINGS) > 0
