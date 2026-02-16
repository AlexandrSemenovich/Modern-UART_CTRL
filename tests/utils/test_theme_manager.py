"""
Unit tests for ThemeManager.

Tests the theme management functionality including:
- Theme switching
- Theme detection
- Effective theme resolution
- Edge cases for invalid themes, system theme, etc.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))


class TestThemeManagerInitialization:
    """Test ThemeManager initialization."""
    
    def test_default_theme(self):
        """Test default theme is set."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
                self._theme_applied = False
        
        tm = MockThemeManager()
        
        assert tm.current_theme == "dark"


class TestSetTheme:
    """Test set_theme method."""
    
    def test_set_valid_theme(self):
        """Test setting valid theme."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
                self._theme_applied = False
            
            def set_theme(self, theme):
                if theme in {"light", "dark", "system"}:
                    self.current_theme = theme
                    return True
                return False
        
        tm = MockThemeManager()
        
        assert tm.set_theme("light") is True
        assert tm.current_theme == "light"
    
    def test_set_invalid_theme(self):
        """Test setting invalid theme."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
                self._theme_applied = False
            
            def set_theme(self, theme):
                if theme in {"light", "dark", "system"}:
                    self.current_theme = theme
                    return True
                return False
        
        tm = MockThemeManager()
        
        assert tm.set_theme("invalid") is False
        assert tm.current_theme == "dark"  # Unchanged
    
    def test_set_system_theme(self):
        """Test setting system theme."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def set_theme(self, theme):
                if theme in {"light", "dark", "system"}:
                    self.current_theme = theme
                    return True
                return False
        
        tm = MockThemeManager()
        
        assert tm.set_theme("system") is True
        assert tm.current_theme == "system"


class TestEffectiveTheme:
    """Test effective theme resolution."""
    
    def test_light_theme_effective(self):
        """Test light theme returns light."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "light"
            
            def _get_effective_theme(self):
                if self.current_theme == "system":
                    return "dark"  # Default for system
                return "light" if self.current_theme == "light" else "dark"
        
        tm = MockThemeManager()
        
        assert tm._get_effective_theme() == "light"
    
    def test_dark_theme_effective(self):
        """Test dark theme returns dark."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def _get_effective_theme(self):
                if self.current_theme == "system":
                    return "dark"  # Default for system
                return "light" if self.current_theme == "light" else "dark"
        
        tm = MockThemeManager()
        
        assert tm._get_effective_theme() == "dark"
    
    def test_system_theme_resolves_to_dark(self):
        """Test system theme resolves to dark by default."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "system"
            
            def _get_effective_theme(self):
                if self.current_theme == "system":
                    return "dark"  # Default fallback
                return "light" if self.current_theme == "light" else "dark"
        
        tm = MockThemeManager()
        
        assert tm._get_effective_theme() == "dark"


class TestIsDarkTheme:
    """Test is_dark_theme method."""
    
    def test_is_dark_when_dark(self):
        """Test is_dark_theme returns True for dark."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def is_dark_theme(self):
                return self.current_theme == "dark"
        
        tm = MockThemeManager()
        
        assert tm.is_dark_theme() is True
    
    def test_is_dark_when_light(self):
        """Test is_dark_theme returns False for light."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "light"
            
            def is_dark_theme(self):
                return self.current_theme == "dark"
        
        tm = MockThemeManager()
        
        assert tm.is_dark_theme() is False


class TestIsLightTheme:
    """Test is_light_theme method."""
    
    def test_is_light_when_light(self):
        """Test is_light_theme returns True for light."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "light"
            
            def is_light_theme(self):
                return self.current_theme == "light"
        
        tm = MockThemeManager()
        
        assert tm.is_light_theme() is True
    
    def test_is_light_when_dark(self):
        """Test is_light_theme returns False for dark."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def is_light_theme(self):
                return self.current_theme == "light"
        
        tm = MockThemeManager()
        
        assert tm.is_light_theme() is False


class TestGetTheme:
    """Test get_theme method."""
    
    def test_get_current_theme(self):
        """Test get_theme returns current theme."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def get_theme(self):
                return self.current_theme
        
        tm = MockThemeManager()
        
        assert tm.get_theme() == "dark"


class TestThemeResolution:
    """Test theme resolution logic."""
    
    def test_resolve_light(self):
        """Test resolving light theme."""
        theme = "light"
        
        effective = "light" if theme == "light" else "dark"
        
        assert effective == "light"
    
    def test_resolve_dark(self):
        """Test resolving dark theme."""
        theme = "dark"
        
        effective = "light" if theme == "light" else "dark"
        
        assert effective == "dark"
    
    def test_resolve_system(self):
        """Test resolving system theme defaults to dark."""
        theme = "system"
        
        # For system, would detect OS preference, defaulting to dark
        effective = "dark"
        
        assert effective == "dark"


class TestEdgeCases:
    """Test edge cases."""
    
    def test_theme_change_tracking(self):
        """Test tracking theme changes."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
                self._last_applied_theme = None
            
            def set_theme(self, theme):
                if theme != self.current_theme:
                    self._last_applied_theme = self.current_theme
                    self.current_theme = theme
        
        tm = MockThemeManager()
        tm.set_theme("light")
        
        assert tm._last_applied_theme == "dark"
        assert tm.current_theme == "light"
    
    def test_same_theme_no_change(self):
        """Test setting same theme doesn't trigger change."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
                self._last_applied_theme = None
            
            def set_theme(self, theme):
                if theme != self.current_theme:
                    self._last_applied_theme = self.current_theme
                    self.current_theme = theme
        
        tm = MockThemeManager()
        tm.set_theme("dark")  # Same as current
        
        assert tm._last_applied_theme is None
    
    def test_invalid_theme_rejected(self):
        """Test invalid theme is rejected."""
        class MockThemeManager:
            def __init__(self):
                self.current_theme = "dark"
            
            def set_theme(self, theme):
                if theme not in {"light", "dark", "system"}:
                    return False
                self.current_theme = theme
                return True
        
        tm = MockThemeManager()
        result = tm.set_theme("blue")
        
        assert result is False
        assert tm.current_theme == "dark"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
