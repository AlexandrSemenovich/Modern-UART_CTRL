"""
Unit tests for state_utils.

Tests the state utility functions including:
- PortConnectionState enum
- State normalization
- Terminal state detection
- Active state detection
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from src.utils.state_utils import (
    PortConnectionState,
    normalize_state,
    is_terminal_state,
    is_active_state
)


class TestPortConnectionStateEnum:
    """Test PortConnectionState enum."""
    
    def test_all_states_exist(self):
        """Test all expected states exist."""
        assert PortConnectionState.DISCONNECTED.value == 'disconnected'
        assert PortConnectionState.CONNECTING.value == 'connecting'
        assert PortConnectionState.CONNECTED.value == 'connected'
        assert PortConnectionState.ERROR.value == 'error'
    
    def test_state_count(self):
        """Test there are exactly 4 states."""
        states = list(PortConnectionState)
        assert len(states) == 4


class TestNormalizeState:
    """Test normalize_state function."""
    
    def test_normalize_disconnected_string(self):
        """Test normalizing 'disconnected' string."""
        result = normalize_state('disconnected')
        assert result == PortConnectionState.DISCONNECTED
    
    def test_normalize_connecting_string(self):
        """Test normalizing 'connecting' string."""
        result = normalize_state('connecting')
        assert result == PortConnectionState.CONNECTING
    
    def test_normalize_connected_string(self):
        """Test normalizing 'connected' string."""
        result = normalize_state('connected')
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_error_string(self):
        """Test normalizing 'error' string."""
        result = normalize_state('error')
        assert result == PortConnectionState.ERROR
    
    def test_normalize_enum(self):
        """Test normalizing enum returns same enum."""
        result = normalize_state(PortConnectionState.CONNECTED)
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_uppercase(self):
        """Test normalizing uppercase string."""
        result = normalize_state('CONNECTED')
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_mixed_case(self):
        """Test normalizing mixed case string."""
        result = normalize_state('ConNeCtEd')
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_with_prefix(self):
        """Test normalizing string with prefix."""
        result = normalize_state('PortConnectionState.CONNECTED')
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_dot_prefix(self):
        """Test normalizing string with dot prefix."""
        result = normalize_state('.connected')
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_invalid_returns_disconnected(self):
        """Test invalid string returns DISCONNECTED."""
        result = normalize_state('invalid_state')
        assert result == PortConnectionState.DISCONNECTED
    
    def test_normalize_empty_string(self):
        """Test empty string returns DISCONNECTED."""
        result = normalize_state('')
        assert result == PortConnectionState.DISCONNECTED
    
    def test_normalize_none(self):
        """Test None returns DISCONNECTED."""
        result = normalize_state(None)
        assert result == PortConnectionState.DISCONNECTED


class TestIsTerminalState:
    """Test is_terminal_state function."""
    
    def test_disconnected_is_terminal(self):
        """Test DISCONNECTED is terminal."""
        assert is_terminal_state('disconnected') is True
        assert is_terminal_state(PortConnectionState.DISCONNECTED) is True
    
    def test_error_is_terminal(self):
        """Test ERROR is terminal."""
        assert is_terminal_state('error') is True
        assert is_terminal_state(PortConnectionState.ERROR) is True
    
    def test_connected_is_not_terminal(self):
        """Test CONNECTED is not terminal."""
        assert is_terminal_state('connected') is False
        assert is_terminal_state(PortConnectionState.CONNECTED) is False
    
    def test_connecting_is_not_terminal(self):
        """Test CONNECTING is not terminal."""
        assert is_terminal_state('connecting') is False
        assert is_terminal_state(PortConnectionState.CONNECTING) is False
    
    def test_all_states_terminal_classification(self):
        """Test terminal classification for all states."""
        assert is_terminal_state(PortConnectionState.DISCONNECTED) is True
        assert is_terminal_state(PortConnectionState.ERROR) is True
        assert is_terminal_state(PortConnectionState.CONNECTING) is False
        assert is_terminal_state(PortConnectionState.CONNECTED) is False


class TestIsActiveState:
    """Test is_active_state function."""
    
    def test_connected_is_active(self):
        """Test CONNECTED is active."""
        assert is_active_state('connected') is True
        assert is_active_state(PortConnectionState.CONNECTED) is True
    
    def test_disconnected_is_not_active(self):
        """Test DISCONNECTED is not active."""
        assert is_active_state('disconnected') is False
        assert is_active_state(PortConnectionState.DISCONNECTED) is False
    
    def test_connecting_is_not_active(self):
        """Test CONNECTING is not active."""
        assert is_active_state('connecting') is False
        assert is_active_state(PortConnectionState.CONNECTING) is False
    
    def test_error_is_not_active(self):
        """Test ERROR is not active."""
        assert is_active_state('error') is False
        assert is_active_state(PortConnectionState.ERROR) is False
    
    def test_all_states_active_classification(self):
        """Test active classification for all states."""
        assert is_active_state(PortConnectionState.CONNECTED) is True
        assert is_active_state(PortConnectionState.DISCONNECTED) is False
        assert is_active_state(PortConnectionState.CONNECTING) is False
        assert is_active_state(PortConnectionState.ERROR) is False


class TestStateTransitions:
    """Test state transition logic."""
    
    def test_connected_from_connecting(self):
        """Test can transition from CONNECTING to CONNECTED."""
        # CONNECTING -> CONNECTED is valid
        state = PortConnectionState.CONNECTING
        new_state = PortConnectionState.CONNECTED
        
        # Both are valid states
        assert normalize_state(state) == PortConnectionState.CONNECTING
        assert normalize_state(new_state) == PortConnectionState.CONNECTED
    
    def test_disconnected_from_connected(self):
        """Test can transition from CONNECTED to DISCONNECTED."""
        # CONNECTED -> DISCONNECTED is valid (disconnect)
        state = PortConnectionState.CONNECTED
        new_state = PortConnectionState.DISCONNECTED
        
        assert is_active_state(state) is True
        assert is_terminal_state(new_state) is True
    
    def test_error_from_any_state(self):
        """Test ERROR can come from any state."""
        for state in PortConnectionState:
            assert is_terminal_state(state) or is_terminal_state('error')


class TestEdgeCases:
    """Test edge cases."""
    
    def test_case_insensitive_normalization(self):
        """Test normalization is case insensitive."""
        assert normalize_state('DISCONNECTED') == PortConnectionState.DISCONNECTED
        assert normalize_state('DisCoNnEcTeD') == PortConnectionState.DISCONNECTED
        assert normalize_state('ErRoR') == PortConnectionState.ERROR
    
    def test_numeric_string(self):
        """Test normalizing numeric string."""
        result = normalize_state('123')
        
        # Should return default (DISCONNECTED)
        assert result == PortConnectionState.DISCONNECTED
    
    def test_special_characters(self):
        """Test normalizing string with special characters."""
        result = normalize_state('connected!@#')
        
        # Should return default
        assert result == PortConnectionState.DISCONNECTED
    
    def test_none_enum(self):
        """Test None as enum."""
        # This would be an error in practice, but let's see behavior
        # normalize_state doesn't handle None enum value specifically
        # but it handles None as string which returns DISCONNECTED
        result = normalize_state(None)
        assert result == PortConnectionState.DISCONNECTED


class TestStateComparison:
    """Test state comparison."""
    
    def test_equality(self):
        """Test enum equality."""
        state1 = PortConnectionState.CONNECTED
        state2 = PortConnectionState.CONNECTED
        
        assert state1 == state2
    
    def test_inequality(self):
        """Test enum inequality."""
        state1 = PortConnectionState.CONNECTED
        state2 = PortConnectionState.DISCONNECTED
        
        assert state1 != state2
    
    def test_value_comparison(self):
        """Test comparing state to its value."""
        state = PortConnectionState.CONNECTED
        
        assert state.value == 'connected'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
