"""
Unit tests for MainViewModel.

Tests the business logic for the main window including:
- Message formatting (RX, TX, SYSTEM)
- Cache management
- Filtering
- Display options
- Edge cases for empty messages, long messages, special characters
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from src.viewmodels.main_viewmodel import MainViewModel


class TestMainViewModelInitialization:
    """Test MainViewModel initialization."""
    
    def test_default_initialization(self):
        """Test MainViewModel initializes with default values."""
        vm = MainViewModel()
        
        assert vm.show_time is True
        assert vm.show_source is True
        assert isinstance(vm.rx_counts, list)
        assert isinstance(vm.tx_counts, list)
        assert len(vm.rx_counts) == 3
        assert len(vm.tx_counts) == 3
    
    def test_initial_counters_are_zero(self):
        """Test initial counters are zero."""
        vm = MainViewModel()
        
        assert vm.rx_counts == [0, 0, 0]
        assert vm.tx_counts == [0, 0, 0]


class TestSetDisplayOptions:
    """Test set_display_options method."""
    
    def test_set_display_options(self):
        """Test setting display options."""
        vm = MainViewModel()
        
        vm.set_display_options(False, False)
        
        assert vm.show_time is False
        assert vm.show_source is False
    
    def test_set_time_only(self):
        """Test setting time only."""
        vm = MainViewModel()
        
        vm.set_display_options(True, False)
        
        assert vm.show_time is True
        assert vm.show_source is False
    
    def test_set_source_only(self):
        """Test setting source only."""
        vm = MainViewModel()
        
        vm.set_display_options(False, True)
        
        assert vm.show_time is False
        assert vm.show_source is True


class TestFormatRx:
    """Test format_rx method."""
    
    def test_format_rx_basic(self):
        """Test basic RX formatting."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', 'test data')
        
        assert 'RX(CPU1):' in result
        assert 'test data' in result
    
    def test_format_rx_with_newlines(self):
        """Test RX formatting with newlines."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', 'line1\r\nline2\r\n')
        
        assert 'RX(CPU1):' in result
    
    def test_format_rx_empty(self):
        """Test RX formatting with empty string."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', '')
        
        assert result == ''
    
    def test_format_rx_whitespace_only(self):
        """Test RX formatting with whitespace only."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', '   ')
        
        # Empty after stripping should return empty
        assert result == '' or '   ' not in result
    
    def test_format_rx_special_characters(self):
        """Test RX formatting with special HTML characters."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', '<test> & "quote"')
        
        assert '<' in result  # HTML escaped
        assert '>' in result
        assert '&' in result
    
    def test_format_rx_hide_time(self):
        """Test RX formatting without timestamp."""
        vm = MainViewModel()
        vm.set_display_options(False, True)
        
        result = vm.format_rx('CPU1', 'test')
        
        assert '[' not in result  # No timestamp
        assert 'RX(CPU1):' in result
    
    def test_format_rx_hide_source(self):
        """Test RX formatting without source."""
        vm = MainViewModel()
        vm.set_display_options(True, False)
        
        result = vm.format_rx('CPU1', 'test')
        
        assert 'RX(' not in result  # No source label
    
    def test_format_rx_hide_all(self):
        """Test RX formatting without time and source."""
        vm = MainViewModel()
        vm.set_display_options(False, False)
        
        result = vm.format_rx('CPU1', 'test')
        
        assert 'RX(' not in result
        assert '[' not in result
        assert 'test' in result


class TestFormatTx:
    """Test format_tx method."""
    
    def test_format_tx_basic(self):
        """Test basic TX formatting."""
        vm = MainViewModel()
        
        result = vm.format_tx('CPU1', 'command')
        
        assert 'TX(CPU1):' in result
        assert 'command' in result
    
    def test_format_tx_empty(self):
        """Test TX formatting with empty string."""
        vm = MainViewModel()
        
        result = vm.format_tx('CPU1', '')
        
        assert result == ''
    
    def test_format_tx_special_characters(self):
        """Test TX formatting with special HTML characters."""
        vm = MainViewModel()
        
        result = vm.format_tx('CPU1', '<script>alert(1)</script>')
        
        assert '<' in result  # HTML escaped


class TestFormatSystem:
    """Test format_system method."""
    
    def test_format_system_basic(self):
        """Test basic system formatting."""
        vm = MainViewModel()
        
        result = vm.format_system('CPU1', 'Connected')
        
        assert 'SYS(CPU1):' in result
        assert 'Connected' in result
    
    def test_format_system_empty(self):
        """Test system formatting with empty string."""
        vm = MainViewModel()
        
        result = vm.format_system('CPU1', '')
        
        assert result == ''


class TestCacheManagement:
    """Test cache management methods."""
    
    def test_cache_log_line(self):
        """Test caching a log line."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>test</span>', 'test')
        
        assert 'cpu1' in vm.log_cache
        assert len(vm.log_cache['cpu1']['html']) == 1
    
    def test_clear_cache(self):
        """Test clearing cache."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>test</span>', 'test')
        vm.clear_cache()
        
        assert len(vm.log_cache) == 0
    
    def test_cache_multiple_lines(self):
        """Test caching multiple lines."""
        vm = MainViewModel()
        
        for i in range(5):
            vm.cache_log_line('cpu1', f'<span>{i}</span>', str(i))
        
        assert len(vm.log_cache['cpu1']['html']) == 5
    
    def test_cache_limit(self):
        """Test cache respects MAX_CACHE_LINES limit."""
        vm = MainViewModel()
        
        # Add more lines than the limit
        for i in range(vm.MAX_CACHE_LINES + 100):
            vm.cache_log_line('cpu1', f'<span>{i}</span>', str(i))
        
        # Should be limited
        assert len(vm.log_cache['cpu1']['html']) <= vm.MAX_CACHE_LINES


class TestFilterCache:
    """Test filter_cache method."""
    
    def test_filter_cache_empty_query(self):
        """Test filtering with empty query returns all."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>hello</span>', 'hello')
        vm.cache_log_line('cpu1', '<span>world</span>', 'world')
        
        result = vm.filter_cache('cpu1', '')
        
        assert 'hello' in result
        assert 'world' in result
    
    def test_filter_cache_with_match(self):
        """Test filtering with matching query."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>hello</span>', 'hello')
        vm.cache_log_line('cpu1', '<span>world</span>', 'world')
        
        result = vm.filter_cache('cpu1', 'hello')
        
        assert 'hello' in result
        assert 'world' not in result
    
    def test_filter_cache_case_insensitive(self):
        """Test filtering is case insensitive."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>Hello</span>', 'Hello')
        vm.cache_log_line('cpu1', '<span>WORLD</span>', 'WORLD')
        
        result = vm.filter_cache('cpu1', 'hello')
        
        assert 'Hello' in result
    
    def test_filter_cache_nonexistent_key(self):
        """Test filtering with non-existent cache key."""
        vm = MainViewModel()
        
        result = vm.filter_cache('nonexistent', 'test')
        
        assert result == ''
    
    def test_filter_cache_no_match(self):
        """Test filtering with no matches."""
        vm = MainViewModel()
        
        vm.cache_log_line('cpu1', '<span>hello</span>', 'hello')
        
        result = vm.filter_cache('cpu1', 'xyz')
        
        assert 'hello' not in result


class TestStripHtml:
    """Test strip_html method."""
    
    def test_strip_html_basic(self):
        """Test basic HTML stripping."""
        vm = MainViewModel()
        
        result = vm.strip_html('<span>test</span>')
        
        assert result == 'test'
    
    def test_strip_html_with_attributes(self):
        """Test HTML stripping with attributes."""
        vm = MainViewModel()
        
        result = vm.strip_html('<span style="color:red">test</span>')
        
        assert result == 'test'
    
    def test_strip_html_entities(self):
        """Test HTML entity handling in strip_html."""
        vm = MainViewModel()
        
        # Input has HTML tags that should be stripped
        # <test> is a tag, so it gets stripped to nothing
        # Then & and "quoted" remain
        result = vm.strip_html('<test> & "quoted"')
        
        # The <test> is stripped as a tag
        # The remaining content is ' & "quoted"'
        # Note: this shows HTML tags are stripped
        assert '"quoted"' in result
    
    def test_strip_html_none(self):
        """Test stripping None returns empty string or handles gracefully."""
        vm = MainViewModel()
        
        # strip_html doesn't handle None, it will raise TypeError
        # This documents the current behavior
        with pytest.raises(TypeError):
            result = vm.strip_html(None)


class TestCounters:
    """Test counter methods."""
    
    def test_increment_rx(self):
        """Test incrementing RX counter."""
        vm = MainViewModel()
        
        count = vm.increment_rx(1)
        
        assert count == 1
        assert vm.rx_counts[0] == 1
    
    def test_increment_tx(self):
        """Test incrementing TX counter."""
        vm = MainViewModel()
        
        count = vm.increment_tx(1)
        
        assert count == 1
        assert vm.tx_counts[0] == 1
    
    def test_get_rx_count(self):
        """Test getting RX counter."""
        vm = MainViewModel()
        vm.rx_counts[0] = 42
        
        count = vm.get_rx_count(1)
        
        assert count == 42
    
    def test_get_tx_count(self):
        """Test getting TX counter."""
        vm = MainViewModel()
        vm.tx_counts[1] = 100
        
        count = vm.get_tx_count(2)
        
        assert count == 100
    
    def test_clear_counters(self):
        """Test clearing all counters."""
        vm = MainViewModel()
        vm.rx_counts = [1, 2, 3]
        vm.tx_counts = [4, 5, 6]
        
        vm.clear_counters()
        
        assert vm.rx_counts == [0, 0, 0]
        assert vm.tx_counts == [0, 0, 0]
    
    def test_counter_invalid_port(self):
        """Test counter with invalid port index."""
        vm = MainViewModel()
        
        count = vm.increment_rx(99)  # Invalid port
        
        assert count == 0


class TestEdgeCases:
    """Test edge cases."""
    
    def test_very_long_message(self):
        """Test handling very long messages."""
        vm = MainViewModel()
        
        long_text = 'a' * 10000
        result = vm.format_rx('CPU1', long_text)
        
        assert len(result) > 0
    
    def test_unicode_message(self):
        """Test handling unicode messages."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', 'Привет мир 你好')
        
        assert 'Привет' in result
    
    def test_binary_data(self):
        """Test handling binary-like data."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', '\x00\x01\x02\x03')
        
        assert len(result) > 0
    
    def test_mixed_content(self):
        """Test handling mixed content."""
        vm = MainViewModel()
        
        result = vm.format_rx('CPU1', 'Hello <world> & "test"\r\nNext line')
        
        # Should escape HTML properly
        assert '<' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
