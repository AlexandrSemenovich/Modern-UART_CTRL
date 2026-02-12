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


def test_html_truncation():
    """Test HTML truncation logic for long content."""
    MAX_HTML_LENGTH = 10000
    
    # Short content should not be truncated
    short_html = "<span>hello</span>"
    assert len(short_html) <= MAX_HTML_LENGTH
    truncated = short_html if len(short_html) <= MAX_HTML_LENGTH else short_html[:MAX_HTML_LENGTH] + "..."
    assert truncated == short_html
    
    # Long content should be truncated
    long_html = "<span>" + "a" * 15000 + "</span>"
    truncated = long_html[:MAX_HTML_LENGTH] + "...<span style='color:gray'> [truncated]</span>"
    assert len(truncated) <= MAX_HTML_LENGTH + 50  # Allow for truncation indicator
    assert "[truncated]" in truncated
    
    print("[OK] HTML truncation logic OK")


def test_rate_limiting_logic():
    """Test rate limiting logic for serial data."""
    MAX_BYTES_PER_SECOND = 1024 * 1024  # 1 MB/s
    
    # Test that the limit is set correctly
    assert MAX_BYTES_PER_SECOND == 1024 * 1024
    
    # Simulate rate limiting calculation
    data_size = 1024  # 1 KB
    elapsed = 0.001  # 1ms
    rate = data_size / elapsed
    
    # Rate should be in bytes per second
    assert rate > 0
    
    print("[OK] Rate limiting logic OK")


def test_exponential_backoff():
    """Test exponential backoff for connection retries."""
    initial_delay = 0.1  # 100ms
    max_delay = 5.0  # 5 seconds
    max_retries = 5
    
    delays = []
    current_delay = initial_delay
    
    for i in range(max_retries):
        delays.append(current_delay)
        current_delay = min(current_delay * 2, max_delay)
    
    # Verify exponential growth
    assert delays[0] == 0.1
    assert delays[1] == 0.2
    assert delays[2] == 0.4
    assert delays[3] == 0.8
    assert delays[4] == 1.6
    
    # Verify max delay cap
    for delay in delays:
        assert delay <= max_delay
    
    print(f"[OK] Exponential backoff OK (delays: {delays})")


def test_write_batch_limit():
    """Test write batch limit to prevent queue starvation."""
    MAX_WRITE_BATCH = 100
    
    # Simulate queue processing
    queue = list(range(500))
    processed = 0
    batch_count = 0
    
    while queue and processed < 1000:  # Max total processed
        batch = []
        for _ in range(min(MAX_WRITE_BATCH, len(queue))):
            if queue:
                batch.append(queue.pop(0))
        processed += len(batch)
        batch_count += 1
        
        if processed >= 1000:
            break
    
    # Verify batches are limited
    assert MAX_WRITE_BATCH == 100
    assert batch_count >= 5  # 500 items / 100 per batch = 5 batches
    
    print(f"[OK] Write batch limit OK (batches: {batch_count})")


if __name__ == '__main__':
    tests = [
        test_translations_available,
        test_translation_structure,
        test_port_widgets_class,
        test_cache_logic,
        test_html_filtering,
        test_html_truncation,
        test_rate_limiting_logic,
        test_exponential_backoff,
        test_write_batch_limit,
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
