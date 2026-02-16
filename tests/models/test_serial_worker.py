"""
Unit tests for SerialWorker model.

Tests the core functionality of the SerialWorker class including:
- Configuration methods
- Write queue handling  
- Connection state management
- Edge cases like empty data, multiple stop calls, etc.
"""

import pytest
import queue
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from src.models.serial_worker import SerialWorker


class TestSerialWorkerInitialization:
    """Test SerialWorker initialization."""
    
    def test_default_initialization(self):
        """Test worker initializes with default values."""
        worker = SerialWorker('CPU1')
        
        assert worker._port_label == 'CPU1'
        assert worker._port_name is None
        assert worker._baud == 115200
        assert isinstance(worker._write_q, queue.Queue)
    
    def test_custom_config_initialization(self):
        """Test worker initializes with custom config."""
        config = {
            'timeout': 0.5,
            'read_interval': 0.01,
            'charset': 'latin-1'
        }
        worker = SerialWorker('CPU2', config)
        
        assert worker._port_label == 'CPU2'
        assert worker._timeout == 0.5
        assert worker._read_interval == 0.01
        assert worker._charset == 'latin-1'


class TestSerialWorkerConfigure:
    """Test SerialWorker configure method."""
    
    def test_configure_sets_port_and_baud(self):
        """Test configure method sets port name and baud rate."""
        worker = SerialWorker('CPU1')
        worker.configure('COM1', 9600)
        
        assert worker._port_name == 'COM1'
        assert worker._baud == 9600
    
    def test_configure_with_timeout(self):
        """Test configure method sets custom timeout."""
        worker = SerialWorker('CPU1')
        worker.configure('COM1', 115200, timeout=1.0)
        
        assert worker._timeout == 1.0
    
    def test_configure_with_charset(self):
        """Test configure method sets charset."""
        worker = SerialWorker('CPU1')
        worker.configure('COM1', 115200, charset='utf-8')
        
        assert worker._charset == 'utf-8'
    
    def test_configure_with_charset_auto_detect(self):
        """Test configure method enables charset auto-detection."""
        worker = SerialWorker('CPU1')
        worker.configure('COM1', 115200, charset_auto_detect=True)
        
        assert worker._charset_auto_detect is True


class TestSerialWorkerConfigureFromDict:
    """Test SerialWorker configure_from_dict method."""
    
    def test_configure_from_dict(self):
        """Test configure_from_dict sets values from dictionary."""
        worker = SerialWorker('CPU1')
        config = {
            'port': 'COM3',
            'baud': 57600,
            'timeout': 0.5,
            'charset': 'ascii'
        }
        worker.configure_from_dict(config)
        
        assert worker._port_name == 'COM3'
        assert worker._baud == 57600
        assert worker._timeout == 0.5
        assert worker._charset == 'ascii'
    
    def test_configure_from_dict_defaults(self):
        """Test configure_from_dict uses defaults for missing values."""
        worker = SerialWorker('CPU1')
        config = {'port': 'COM1'}
        worker.configure_from_dict(config)
        
        assert worker._port_name == 'COM1'
        assert worker._baud == 115200  # default


class TestSerialWorkerWrite:
    """Test SerialWorker write method."""
    
    def test_write_enqueue_data(self):
        """Test write method adds data to queue."""
        worker = SerialWorker('CPU1')
        worker.write('TEST')
        
        item = worker._write_q.get_nowait()
        assert item == 'TEST'
    
    def test_write_empty_string(self):
        """Test writing empty string does not crash."""
        worker = SerialWorker('CPU1')
        # Should not raise
        worker.write('')
    
    def test_write_none(self):
        """Test writing None does not crash."""
        worker = SerialWorker('CPU1')
        # Should not raise
        worker.write(None)
    
    def test_write_when_disconnected(self):
        """Test write when port is not connected."""
        worker = SerialWorker('CPU1')
        # Port not configured, but write should still work
        worker.write('DATA')
        
        item = worker._write_q.get_nowait()
        assert item == 'DATA'
    
    def test_write_unicode_data(self):
        """Test writing unicode data."""
        worker = SerialWorker('CPU1')
        worker.write('Привет мир')
        
        item = worker._write_q.get_nowait()
        assert item == 'Привет мир'
    
    def test_write_special_characters(self):
        """Test writing special characters."""
        worker = SerialWorker('CPU1')
        worker.write('Test\r\n\t\b')
        
        item = worker._write_q.get_nowait()
        assert item == 'Test\r\n\t\b'


class TestSerialWorkerProperties:
    """Test SerialWorker property methods."""
    
    def test_is_connected_when_not_connected(self):
        """Test is_connected returns False when not connected."""
        worker = SerialWorker('CPU1')
        assert worker.is_connected is False
    
    def test_charset_property(self):
        """Test charset property returns configured charset."""
        worker = SerialWorker('CPU1')
        worker._charset = 'utf-8'
        
        assert worker.charset == 'utf-8'
    
    def test_detected_charset_property(self):
        """Test detected_charset property."""
        worker = SerialWorker('CPU1')
        
        assert worker.detected_charset is None
    
    def test_is_charset_auto_detect_property(self):
        """Test is_charset_auto_detect property."""
        worker = SerialWorker('CPU1')
        
        assert worker.is_charset_auto_detect is False
    
    def test_connection_attempts_property(self):
        """Test connection_attempts property."""
        worker = SerialWorker('CPU1')
        
        assert worker.connection_attempts == 0


class TestSerialWorkerEdgeCases:
    """Test edge cases for SerialWorker."""
    
    def test_stop_multiple_calls(self):
        """Test multiple stop calls don't cause errors."""
        worker = SerialWorker('CPU1')
        
        # Should not raise
        worker.stop()
        worker.stop()
        worker.stop()
    
    def test_stop_sets_running_flag(self):
        """Test stop method sets running flag."""
        worker = SerialWorker('CPU1')
        worker._running = True
        
        worker.stop()
        
        assert worker._should_stop is True
    
    def test_configure_invalid_baud(self):
        """Test configure with unusual baud rate."""
        worker = SerialWorker('CPU1')
        worker.configure('COM1', 300)  # Valid but unusual
        
        assert worker._baud == 300
    
    def test_configure_very_long_port_name(self):
        """Test configure with very long port name."""
        worker = SerialWorker('CPU1')
        long_name = 'A' * 1000
        worker.configure(long_name, 9600)
        
        assert worker._port_name == long_name
    
    def test_max_buffer_size_constant(self):
        """Test MAX_BUFFER_SIZE constant exists."""
        worker = SerialWorker('CPU1')
        
        assert hasattr(worker, 'MAX_BUFFER_SIZE')
        assert worker.MAX_BUFFER_SIZE == 65536
    
    def test_max_write_size_constant(self):
        """Test MAX_WRITE_SIZE constant exists."""
        worker = SerialWorker('CPU1')
        
        assert hasattr(worker, 'MAX_WRITE_SIZE')
        assert worker.MAX_WRITE_SIZE == 65536


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
