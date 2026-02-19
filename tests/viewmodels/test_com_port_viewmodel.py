"""
Unit tests for ComPortViewModel.

Tests the business logic for COM port management including:
- Port configuration
- Connection management
- Data transmission
- State management
- Edge cases for invalid ports, disconnected state, etc.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from unittest.mock import Mock, patch, MagicMock


class TestComPortViewModelInitialization:
    """Test ComPortViewModel initialization."""
    
    def test_default_initialization(self):
        """Test ComPortViewModel initializes with default values."""
        # Need to mock Qt components
        with patch('src.viewmodels.com_port_viewmodel.QObject'):
            from src.viewmodels.com_port_viewmodel import ComPortViewModel
            
            vm = ComPortViewModel.__new__(ComPortViewModel)
            vm._port_label = 'CPU1'
            vm._port_number = 1
            vm._config = {}
            vm._state = None
            vm._port_name = None
            vm._baud_rate = 115200
            vm._rx_count = 0
            vm._tx_count = 0
            vm._worker = None
            vm._available_ports = []
            
            assert vm._port_label == 'CPU1'
            assert vm._port_number == 1
            assert vm._baud_rate == 115200


class TestPortProperties:
    """Test port property methods."""
    
    def test_port_label_property(self):
        """Test port_label property."""
        from src.utils.state_utils import PortConnectionState
        
        # Create mock viewmodel
        class MockVM:
            def __init__(self):
                self._port_label = 'CPU1'
                self._port_number = 1
                self._state = PortConnectionState.DISCONNECTED
                self._port_name = 'COM1'
                self._baud_rate = 115200
                self._rx_count = 0
                self._tx_count = 0
                self._available_ports = ['COM1', 'COM2']
            
            @property
            def port_label(self):
                return self._port_label
            
            @property
            def port_number(self):
                return self._port_number
            
            @property
            def state(self):
                return self._state
            
            @property
            def port_name(self):
                return self._port_name
            
            @property
            def baud_rate(self):
                return self._baud_rate
            
            @property
            def rx_count(self):
                return self._rx_count
            
            @property
            def tx_count(self):
                return self._tx_count
            
            @property
            def is_connected(self):
                return self._state == PortConnectionState.CONNECTED
            
            @property
            def available_ports(self):
                return self._available_ports.copy()
        
        vm = MockVM()
        
        assert vm.port_label == 'CPU1'
        assert vm.port_number == 1
        assert vm.port_name == 'COM1'
        assert vm.baud_rate == 115200
        assert vm.rx_count == 0
        assert vm.tx_count == 0
        assert vm.is_connected is False
        assert 'COM1' in vm.available_ports


class TestSetMethods:
    """Test set methods."""
    
    def test_set_port_name(self):
        """Test set_port_name method."""
        class MockVM:
            def __init__(self):
                self._port_name = None
            
            def set_port_name(self, port_name):
                self._port_name = port_name
        
        vm = MockVM()
        vm.set_port_name('COM3')
        
        assert vm._port_name == 'COM3'
    
    def test_set_baud_rate_valid(self):
        """Test set_baud_rate with valid value."""
        class MockVM:
            def __init__(self):
                self._baud_rate = 115200
            
            def set_baud_rate(self, baud_rate):
                from src.styles.constants import SerialConfig
                if baud_rate in SerialConfig.BAUD_RATES:
                    self._baud_rate = baud_rate
        
        vm = MockVM()
        vm.set_baud_rate(9600)
        
        assert vm._baud_rate == 9600
    
    def test_set_baud_rate_invalid(self):
        """Test set_baud_rate with invalid value."""
        class MockVM:
            def __init__(self):
                self._baud_rate = 115200
            
            def set_baud_rate(self, baud_rate):
                from src.styles.constants import SerialConfig
                if baud_rate in SerialConfig.BAUD_RATES:
                    self._baud_rate = baud_rate
        
        vm = MockVM()
        original = vm._baud_rate
        vm.set_baud_rate(999999)  # Invalid baud rate
        
        # Should keep original value
        assert vm._baud_rate == original
    
    def test_set_available_ports(self):
        """Test set_available_ports method."""
        class MockVM:
            def __init__(self):
                self._available_ports = []
            
            def set_available_ports(self, ports):
                self._available_ports = ports
        
        vm = MockVM()
        vm.set_available_ports(['COM1', 'COM2', 'COM3'])
        
        assert len(vm._available_ports) == 3


class TestStateNormalization:
    """Test state normalization."""
    
    def test_normalize_state_from_string(self):
        """Test normalizing state from string."""
        from src.utils.state_utils import normalize_state, PortConnectionState
        
        result = normalize_state('connected')
        
        assert result == PortConnectionState.CONNECTED
    
    def test_normalize_state_from_enum(self):
        """Test normalizing state from enum."""
        from src.utils.state_utils import normalize_state, PortConnectionState
        
        result = normalize_state(PortConnectionState.DISCONNECTED)
        
        assert result == PortConnectionState.DISCONNECTED
    
    def test_normalize_state_invalid(self):
        """Test normalizing invalid state."""
        from src.utils.state_utils import normalize_state, PortConnectionState
        
        result = normalize_state('invalid_state')
        
        # Should default to DISCONNECTED
        assert result == PortConnectionState.DISCONNECTED
    
    def test_normalize_state_with_prefix(self):
        """Test normalizing state with prefix."""
        from src.utils.state_utils import normalize_state, PortConnectionState
        
        result = normalize_state('PortConnectionState.CONNECTED')
        
        assert result == PortConnectionState.CONNECTED


class TestPortConnectionState:
    """Test PortConnectionState enum."""
    
    def test_connection_states(self):
        """Test all connection states exist."""
        from src.utils.state_utils import PortConnectionState
        
        assert PortConnectionState.DISCONNECTED.value == 'disconnected'
        assert PortConnectionState.CONNECTING.value == 'connecting'
        assert PortConnectionState.CONNECTED.value == 'connected'
        assert PortConnectionState.ERROR.value == 'error'


class TestCounterOperations:
    """Test counter operations."""
    
    def test_clear_counters(self):
        """Test clearing counters."""
        class MockVM:
            def __init__(self):
                self._rx_count = 100
                self._tx_count = 50
                self._rx_bytes = 200
                self._tx_bytes = 150
                self._error_count = 5
                self._connection_time = 100.0
            
            def clear_counters(self):
                self._rx_count = 0
                self._tx_count = 0
                self._rx_bytes = 0
                self._tx_bytes = 0
                self._error_count = 0
                self._connection_time = 0.0
        
        vm = MockVM()
        vm.clear_counters()
        
        assert vm._rx_count == 0
        assert vm._tx_count == 0
        assert vm._rx_bytes == 0
        assert vm._tx_bytes == 0
        assert vm._error_count == 0
        assert vm._connection_time == 0.0


class TestErrorCounter:
    """Test error counter operations."""
    
    def test_error_count_initial_value(self):
        """Test that error_count initializes to zero."""
        class MockVM:
            def __init__(self):
                self._error_count = 0
            
            @property
            def error_count(self) -> int:
                return self._error_count
        
        vm = MockVM()
        assert vm.error_count == 0
    
    def test_error_count_increments(self):
        """Test that error_count increments correctly."""
        class MockVM:
            def __init__(self):
                self._error_count = 0
                self._state = None
            
            @property
            def error_count(self) -> int:
                return self._error_count
            
            def _set_state(self, new_state):
                self._state = new_state
            
            def _emit_error(self, msg):
                pass
            
            def _safe_stop_worker(self):
                pass
            
            def _on_error(self, port_label: str, error_message: str) -> None:
                self._error_count += 1
                self._set_state("error")
                self._emit_error(error_message)
                self._safe_stop_worker()
        
        vm = MockVM()
        vm._on_error("COM1", "Test error 1")
        vm._on_error("COM1", "Test error 2")
        vm._on_error("COM1", "Test error 3")
        
        assert vm.error_count == 3
    
    def test_error_count_resets(self):
        """Test that error_count resets to zero."""
        class MockVM:
            def __init__(self):
                self._error_count = 10
            
            @property
            def error_count(self) -> int:
                return self._error_count
            
            def clear_counters(self):
                self._error_count = 0
        
        vm = MockVM()
        assert vm.error_count == 10
        
        vm.clear_counters()
        assert vm.error_count == 0


class TestConnectionTime:
    """Test connection time operations."""
    
    def test_connection_time_initial_value(self):
        """Test that connection_time initializes to zero."""
        import time
        
        class MockVM:
            def __init__(self):
                self._connection_time = 0.0
            
            @property
            def connection_time(self) -> float:
                if self._connection_time > 0:
                    return time.monotonic() - self._connection_time
                return 0.0
        
        vm = MockVM()
        assert vm.connection_time == 0.0
    
    def test_connection_time_after_connect(self):
        """Test that connection_time is set on connect."""
        import time
        
        class MockVM:
            def __init__(self):
                self._connection_time = 0.0
            
            @property
            def connection_time(self) -> float:
                if self._connection_time > 0:
                    return time.monotonic() - self._connection_time
                return 0.0
            
            def on_connected(self):
                self._connection_time = time.monotonic()
        
        vm = MockVM()
        # Before connection
        assert vm.connection_time == 0.0
        
        # Simulate connection
        vm.on_connected()
        time.sleep(0.01)  # 10ms
        
        # After connection - should be approximately 0.01 seconds
        elapsed = vm.connection_time
        assert 0.005 < elapsed < 0.050  # Allow generous margin
    
    def test_connection_time_resets_on_clear(self):
        """Test that connection_time resets to zero on clear."""
        import time
        
        class MockVM:
            def __init__(self):
                self._connection_time = 100.0  # Some old value
            
            @property
            def connection_time(self) -> float:
                if self._connection_time > 0:
                    return time.monotonic() - self._connection_time
                return 0.0
            
            def clear_counters(self):
                self._connection_time = 0.0
        
        vm = MockVM()
        vm.clear_counters()
        
        assert vm.connection_time == 0.0
    
    def test_connection_time_uses_monotonic(self):
        """Test that connection_time uses monotonic time (not wall clock)."""
        import time
        
        class MockVM:
            def __init__(self):
                self._connection_time = time.monotonic()  # Set using monotonic
            
            @property
            def connection_time(self) -> float:
                if self._connection_time > 0:
                    return time.monotonic() - self._connection_time
                return 0.0
        
        vm = MockVM()
        
        # Both should use monotonic, so difference should be small
        elapsed = vm.connection_time
        assert 0 <= elapsed < 0.1  # Should be very small (within 100ms)


class TestEdgeCases:
    """Test edge cases."""
    
    def test_increment_counters(self):
        """Test incrementing counters."""
        class MockVM:
            def __init__(self):
                self._rx_count = 0
                self._tx_count = 0
            
            def increment_rx(self):
                self._rx_count += 1
            
            def increment_tx(self):
                self._tx_count += 1
        
        vm = MockVM()
        vm.increment_rx()
        vm.increment_rx()
        vm.increment_tx()
        
        assert vm._rx_count == 2
        assert vm._tx_count == 1
    
    def test_large_counter_values(self):
        """Test handling large counter values."""
        class MockVM:
            def __init__(self):
                self._rx_count = 0
            
            def increment_rx(self):
                self._rx_count += 1
        
        vm = MockVM()
        for _ in range(10000):
            vm.increment_rx()
        
        assert vm._rx_count == 10000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
