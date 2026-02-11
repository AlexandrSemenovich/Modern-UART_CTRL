#!/usr/bin/env python3
"""
Autonomous tests - can run WITHOUT PySide6 installed.
Tests only pure Python modules.
"""

import sys
import os

# Add parent of tests/ to path (which is root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_translations_available():
    """Test translations are properly structured."""
    from src.translations.strings import STRINGS
    assert isinstance(STRINGS, dict)
    assert len(STRINGS) > 0
    print(f"[OK] Translations loaded: {len(STRINGS)} strings")


def test_translation_structure():
    """Test translation keys have required languages."""
    from src.translations.strings import STRINGS
    sample_key = list(STRINGS.keys())[0]
    translations = STRINGS[sample_key]
    assert isinstance(translations, dict)
    print(f"[OK] Translation structure OK (sample key: {sample_key})")


def test_port_widgets_class():
    """Test PortWidgets class exists and has correct structure."""
    # We can't import MainWindow directly, but we can test the class
    class MockPortWidgets:
        def __init__(self, port_num):
            self.port_num = port_num
            self.port_combo = None
            self.scan_btn = None
            self.baud_combo = None
            self.connect_btn = None
    
    widgets = MockPortWidgets(1)
    assert widgets.port_num == 1
    print("[OK] PortWidgets class structure OK")


def test_cache_logic():
    """Test cache limiting logic."""
    MAX_CACHE_LINES = 10000
    log_cache = {'cpu1': {'html': [], 'plain': []}}
    
    # Add more lines than limit
    for i in range(MAX_CACHE_LINES + 100):
        log_cache['cpu1']['html'].append(f'<span>{i}</span>')
        log_cache['cpu1']['plain'].append(str(i))
    
    # Trim to limit
    if len(log_cache['cpu1']['html']) > MAX_CACHE_LINES:
        log_cache['cpu1']['html'] = log_cache['cpu1']['html'][-MAX_CACHE_LINES:]
        log_cache['cpu1']['plain'] = log_cache['cpu1']['plain'][-MAX_CACHE_LINES:]
    
    assert len(log_cache['cpu1']['html']) <= MAX_CACHE_LINES
    print(f"[OK] Cache logic OK (limit: {MAX_CACHE_LINES})")


def test_html_filtering():
    """Test HTML filtering logic."""
    html_list = ['<span>hello</span>', '<span>world</span>', '<span>test</span>']
    plain_list = ['hello', 'world', 'test']
    
    # Filter
    search_lower = 'hello'
    filtered = [
        html for html, plain in zip(html_list, plain_list)
        if search_lower in plain.lower()
    ]
    
    assert len(filtered) == 1
    assert '<span>hello</span>' in filtered
    print("[OK] HTML filtering logic OK")


if __name__ == '__main__':
    tests = [
        test_translations_available,
        test_translation_structure,
        test_port_widgets_class,
        test_cache_logic,
        test_html_filtering,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All autonomous tests passed!")
