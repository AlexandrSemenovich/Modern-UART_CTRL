"""
Unit tests for ConfigLoader.

Tests the configuration loading functionality including:
- Loading colors for different themes
- Loading button colors
- Loading font and size configurations
- Edge cases for missing/non-existent themes
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from src.utils.config_loader import ConfigLoader, ThemeColors, ButtonColors, FontConfig, SizeConfig


class TestConfigLoaderInitialization:
    """Test ConfigLoader initialization."""
    
    def test_default_initialization(self):
        """Test ConfigLoader initializes with defaults."""
        loader = ConfigLoader()
        
        assert loader._config is not None
        assert 'dark' in loader._default_colors
        assert 'light' in loader._default_colors
    
    def test_default_colors_structure(self):
        """Test default colors have correct structure."""
        loader = ConfigLoader()
        
        dark_colors = loader._default_colors['dark']
        assert hasattr(dark_colors, 'timestamp')
        assert hasattr(dark_colors, 'rx_text')
        assert hasattr(dark_colors, 'rx_label')
        assert hasattr(dark_colors, 'tx_text')
        assert hasattr(dark_colors, 'tx_label')
        assert hasattr(dark_colors, 'sys_text')
        assert hasattr(dark_colors, 'sys_label')


class TestGetColors:
    """Test get_colors method."""
    
    def test_get_dark_colors(self):
        """Test getting dark theme colors."""
        loader = ConfigLoader()
        colors = loader.get_colors('dark')
        
        assert isinstance(colors, ThemeColors)
        assert colors.timestamp is not None
        assert colors.rx_text is not None
    
    def test_get_light_colors(self):
        """Test getting light theme colors."""
        loader = ConfigLoader()
        colors = loader.get_colors('light')
        
        assert isinstance(colors, ThemeColors)
        assert colors.timestamp is not None
    
    def test_get_nonexistent_theme(self):
        """Test getting colors for non-existent theme falls back to dark."""
        loader = ConfigLoader()
        colors = loader.get_colors('nonexistent')
        
        # Should fall back to dark
        assert isinstance(colors, ThemeColors)
        assert colors.timestamp is not None


class TestGetButtonColors:
    """Test get_button_colors method."""
    
    def test_get_dark_button_colors(self):
        """Test getting dark theme button colors."""
        loader = ConfigLoader()
        colors = loader.get_button_colors('dark')
        
        assert isinstance(colors, ButtonColors)
        assert colors.command_combo_active is not None
        assert colors.command_cpu1_active is not None
    
    def test_get_light_button_colors(self):
        """Test getting light theme button colors."""
        loader = ConfigLoader()
        colors = loader.get_button_colors('light')
        
        assert isinstance(colors, ButtonColors)
        assert colors.command_combo_active is not None
    
    def test_get_nonexistent_theme_button_colors(self):
        """Test getting button colors for non-existent theme."""
        loader = ConfigLoader()
        colors = loader.get_button_colors('invalid_theme')
        
        # Should fall back to dark
        assert isinstance(colors, ButtonColors)


class TestGetFonts:
    """Test get_fonts method."""
    
    def test_get_fonts_defaults(self):
        """Test getting fonts with defaults."""
        loader = ConfigLoader()
        fonts = loader.get_fonts()
        
        assert isinstance(fonts, FontConfig)
        assert fonts.default_family is not None
        assert fonts.default_size > 0


class TestGetSizes:
    """Test get_sizes method."""
    
    def test_get_sizes_defaults(self):
        """Test getting sizes with defaults."""
        loader = ConfigLoader()
        sizes = loader.get_sizes()
        
        assert isinstance(sizes, SizeConfig)
        assert sizes.window_min_width > 0
        assert sizes.window_min_height > 0


class TestGetSerialConfig:
    """Test get_serial_config method."""
    
    def test_get_serial_config(self):
        """Test getting serial configuration."""
        loader = ConfigLoader()
        config = loader.get_serial_config()
        
        assert isinstance(config, dict)


class TestGetSerialTiming:
    """Test get_serial_timing method."""
    
    def test_get_serial_timing_defaults(self):
        """Test getting serial timing with defaults."""
        loader = ConfigLoader()
        timing = loader.get_serial_timing()
        
        assert isinstance(timing, dict)
        assert 'default_read_interval' in timing
        assert 'connection_timeout' in timing
        assert 'max_connection_attempts' in timing


class TestGetConsoleConfig:
    """Test get_console_config method."""
    
    def test_get_console_config_defaults(self):
        """Test getting console config with defaults."""
        loader = ConfigLoader()
        config = loader.get_console_config()
        
        assert config.max_cache_lines > 0
        assert config.max_html_length > 0


class TestGetAppVersion:
    """Test get_app_version method."""
    
    def test_get_app_version(self):
        """Test getting application version."""
        loader = ConfigLoader()
        version = loader.get_app_version()
        
        assert isinstance(version, str)


class TestGetDefaultTheme:
    """Test get_default_theme method."""
    
    def test_get_default_theme(self):
        """Test getting default theme."""
        loader = ConfigLoader()
        theme = loader.get_default_theme()
        
        assert isinstance(theme, str)
        assert theme in ('light', 'dark', 'system')


class TestParseIntValue:
    """Test _parse_int_value helper method."""
    
    def test_parse_valid_int(self):
        """Test parsing valid integer string."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("123", 0)
        assert result == 123
    
    def test_parse_int_with_comment(self):
        """Test parsing integer with inline comment."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("100; comment", 0)
        assert result == 100
    
    def test_parse_int_with_space(self):
        """Test parsing integer with spaces."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("  500  ", 0)
        assert result == 500
    
    def test_parse_int_with_underscore(self):
        """Test parsing integer with underscore."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("1_000", 0)
        assert result == 1000
    
    def test_parse_invalid_returns_default(self):
        """Test parsing invalid value returns default."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("not_a_number", 42)
        assert result == 42
    
    def test_parse_none_returns_default(self):
        """Test parsing None returns default."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value(None, 99)
        assert result == 99
    
    def test_parse_empty_string_returns_default(self):
        """Test parsing empty string returns default."""
        loader = ConfigLoader()
        
        result = loader._parse_int_value("", 77)
        assert result == 77


class TestEdgeCases:
    """Test edge cases for ConfigLoader."""
    
    def test_get_section_nonexistent(self):
        """Test getting non-existent section."""
        loader = ConfigLoader()
        
        section = loader._get_section('nonexistent_section')
        assert section == {}
    
    def test_get_palette_colors(self):
        """Test getting palette colors."""
        loader = ConfigLoader()
        
        palette = loader.get_palette_colors('dark')
        assert palette is not None
        assert hasattr(palette, 'window')
        assert hasattr(palette, 'window_text')
    
    def test_get_ports_config(self):
        """Test getting ports configuration."""
        loader = ConfigLoader()
        
        ports = loader.get_ports_config()
        assert isinstance(ports, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
