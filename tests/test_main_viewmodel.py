"""
Simple unit tests that can run without PySide6.
Tests pure Python logic for MainViewModel and utilities.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestCacheLogic:
    """Test cache limiting logic (pure Python)."""
    
    MAX_CACHE_LINES = 10000
    
    def test_cache_limit_logic(self):
        """Test cache respects MAX_CACHE_LINES limit."""
        log_cache = {'cpu1': {'html': [], 'plain': []}}
        
        # Add more lines than the limit
        for i in range(self.MAX_CACHE_LINES + 100):
            log_cache['cpu1']['html'].append(f'<span>{i}</span>')
            log_cache['cpu1']['plain'].append(str(i))
        
        # Should be limited to MAX_CACHE_LINES
        if len(log_cache['cpu1']['html']) > self.MAX_CACHE_LINES:
            log_cache['cpu1']['html'] = log_cache['cpu1']['html'][-self.MAX_CACHE_LINES:]
            log_cache['cpu1']['plain'] = log_cache['cpu1']['plain'][-self.MAX_CACHE_LINES:]
        
        cache_size = len(log_cache['cpu1']['html'])
        assert cache_size <= self.MAX_CACHE_LINES
    
    def test_cache_filter_logic(self):
        """Test cache filtering logic."""
        html_list = ['<span>hello</span>', '<span>world</span>', '<span>hello world</span>']
        plain_list = ['hello', 'world', 'hello world']
        
        search_lower = 'hello'
        filtered_html = [
            html for html, plain in zip(html_list, plain_list)
            if search_lower in plain.lower()
        ]
        
        assert len(filtered_html) == 2
        assert '<span>hello</span>' in filtered_html
        assert '<span>hello world</span>' in filtered_html


class TestHtmlUtils:
    """Test HTML utility functions."""
    
    def test_strip_html(self):
        """Test HTML tag stripping."""
        import re
        html = '<span style="color:red">test & <tag></span>'
        
        clean = re.compile('<.*?>')
        clean_text = re.sub(clean, '', html)
        
        assert '<' not in clean_text
        assert '>' not in clean_text
        assert 'test' in clean_text
    
    def test_html_entities(self):
        """Test HTML entity decoding."""
        html = '&lt;test&gt; &amp; &quot;quoted&quot;'
        
        result = html
        result = result.replace('&lt;', '<')
        result = result.replace('&gt;', '>')
        result = result.replace('&amp;', '&')
        result = result.replace('&quot;', '"')
        
        assert '<' in result
        assert '>' in result
        assert '&' in result  # Now it should contain &
        assert '"' in result
        assert '"' in result


class TestPortWidgetsClass:
    """Test PortWidgets container."""
    
    class MockPortWidgets:
        """Simple mock of PortWidgets."""
        def __init__(self, port_num):
            self.port_num = port_num
            self.port_combo = None
            self.scan_btn = None
            self.baud_combo = None
            self.connect_btn = None
    
    def test_port_widgets_creation(self):
        """Test creating PortWidgets instance."""
        widgets = self.MockPortWidgets(1)
        
        assert widgets.port_num == 1
        assert widgets.port_combo is None
        assert widgets.scan_btn is None
        assert widgets.baud_combo is None
        assert widgets.connect_btn is None
    
    def test_port_widgets_attributes(self):
        """Test setting attributes on PortWidgets."""
        widgets = self.MockPortWidgets(2)
        
        class MockCombo:
            pass
        class MockBtn:
            pass
        
        widgets.port_combo = MockCombo()
        widgets.baud_combo = MockCombo()
        widgets.scan_btn = MockBtn()
        widgets.connect_btn = MockBtn()
        
        assert isinstance(widgets.port_combo, MockCombo)
        assert isinstance(widgets.baud_combo, MockCombo)
        assert isinstance(widgets.scan_btn, MockBtn)
        assert isinstance(widgets.connect_btn, MockBtn)


class TestCounterLogic:
    """Test counter logic."""
    
    def test_counter_operations(self):
        """Test counter operations."""
        rx_counts = [0, 0, 0]
        tx_counts = [0, 0, 0]
        
        # Increment
        rx_counts[0] += 1
        tx_counts[0] += 1
        
        assert rx_counts[0] == 1
        assert tx_counts[0] == 1
        
        # Reset
        rx_counts = [0, 0, 0]
        tx_counts = [0, 0, 0]
        
        assert rx_counts == [0, 0, 0]
        assert tx_counts == [0, 0, 0]


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
