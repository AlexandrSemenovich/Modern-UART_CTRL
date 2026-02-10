#!/usr/bin/env python3
"""
Structure tests (moved to tests/)
"""

def test_translations_available():
    from src.translations.strings import STRINGS
    assert isinstance(STRINGS, dict)

def test_views_import():
    from src.views.main_window import MainWindow
    assert MainWindow is not None
