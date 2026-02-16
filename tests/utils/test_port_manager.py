"""
Unit tests for PortManager.

Tests the thread-safe singleton port manager including:
- Acquiring and releasing ports
- Checking port status
- Thread safety
- Edge cases for duplicate acquire, releasing non-acquired ports, etc.
"""

import pytest
import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))


class TestPortManagerSingleton:
    """Test PortManager singleton behavior."""
    
    def test_singleton_instance(self):
        """Test PortManager returns singleton instance."""
        from src.utils.port_manager import PortManager
        
        pm1 = PortManager()
        pm2 = PortManager()
        
        assert pm1 is pm2


class TestPortManagerAcquire:
    """Test acquire method."""
    
    def test_acquire_port(self):
        """Test acquiring a port."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()  # Start fresh
        
        result = pm.acquire('COM1')
        
        assert result is True
        assert pm.is_in_use('COM1')
    
    def test_acquire_same_port_twice(self):
        """Test acquiring same port twice returns False."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        result = pm.acquire('COM1')
        
        assert result is False
    
    def test_acquire_different_ports(self):
        """Test acquiring different ports."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        assert pm.acquire('COM1') is True
        assert pm.acquire('COM2') is True
        assert pm.acquire('COM3') is True
    
    def test_acquire_after_release(self):
        """Test acquiring port after release."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.release('COM1')
        result = pm.acquire('COM1')
        
        assert result is True


class TestPortManagerRelease:
    """Test release method."""
    
    def test_release_acquired_port(self):
        """Test releasing an acquired port."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.release('COM1')
        
        assert pm.is_in_use('COM1') is False
    
    def test_release_non_acquired_port(self):
        """Test releasing a port that was never acquired."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        # Should not raise
        pm.release('COM1')
        
        assert pm.is_in_use('COM1') is False
    
    def test_release_multiple_times(self):
        """Test releasing port multiple times."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.release('COM1')
        pm.release('COM1')  # Should not raise
        
        assert pm.is_in_use('COM1') is False


class TestPortManagerIsInUse:
    """Test is_in_use method."""
    
    def test_in_use_after_acquire(self):
        """Test port shows as in use after acquire."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        
        assert pm.is_in_use('COM1') is True
    
    def test_not_in_use_when_not_acquired(self):
        """Test port shows as not in use when not acquired."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        assert pm.is_in_use('COM1') is False
    
    def test_not_in_use_after_release(self):
        """Test port shows as not in use after release."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.release('COM1')
        
        assert pm.is_in_use('COM1') is False


class TestPortManagerGetActivePorts:
    """Test get_active_ports method."""
    
    def test_get_active_ports_empty(self):
        """Test getting active ports when none acquired."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        ports = pm.get_active_ports()
        
        assert len(ports) == 0
    
    def test_get_active_ports_single(self):
        """Test getting active ports with one port."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        ports = pm.get_active_ports()
        
        assert 'COM1' in ports
        assert len(ports) == 1
    
    def test_get_active_ports_multiple(self):
        """Test getting active ports with multiple ports."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.acquire('COM2')
        pm.acquire('COM3')
        ports = pm.get_active_ports()
        
        assert len(ports) == 3
        assert 'COM1' in ports
        assert 'COM2' in ports
        assert 'COM3' in ports
    
    def test_get_active_ports_returns_copy(self):
        """Test get_active_ports returns a copy."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        ports = pm.get_active_ports()
        
        # Modify returned set
        ports.add('COM2')
        
        # Original should be unchanged
        assert 'COM2' not in pm.get_active_ports()


class TestPortManagerClear:
    """Test clear method."""
    
    def test_clear_removes_all_ports(self):
        """Test clear removes all active ports."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('COM1')
        pm.acquire('COM2')
        pm.clear()
        
        assert len(pm.get_active_ports()) == 0


class TestPortManagerThreadSafety:
    """Test thread safety of PortManager."""
    
    def test_concurrent_acquire(self):
        """Test concurrent acquire operations."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        results = []
        
        def acquire_port(port):
            result = pm.acquire(port)
            results.append((port, result))
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=acquire_port, args=(f'COM{i}',))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # All should succeed
        assert len([r for r in results if r[1]]) == 5
    
    def test_concurrent_acquire_same_port(self):
        """Test concurrent acquire on same port."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        results = []
        
        def try_acquire():
            result = pm.acquire('COM1')
            results.append(result)
        
        threads = [threading.Thread(target=try_acquire) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Only one should succeed
        assert results.count(True) == 1
        assert results.count(False) == 4


class TestEdgeCases:
    """Test edge cases."""
    
    def test_acquire_empty_string(self):
        """Test acquiring port with empty string."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        result = pm.acquire('')
        
        # Should work (empty string is valid)
        assert pm.is_in_use('') is True
    
    def test_acquire_none(self):
        """Test acquiring port with None."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        result = pm.acquire(None)
        
        # Should work (None converted to string)
        assert pm.is_in_use(None) is True
    
    def test_acquire_special_characters(self):
        """Test acquiring port with special characters."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        result = pm.acquire('/dev/ttyUSB0')
        
        assert result is True
    
    def test_case_sensitivity(self):
        """Test port names are case sensitive."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('com1')
        
        assert pm.is_in_use('com1') is True
        assert pm.is_in_use('COM1') is False
    
    def test_release_different_case(self):
        """Test releasing port with different case."""
        from src.utils.port_manager import PortManager
        
        pm = PortManager()
        pm.clear()
        
        pm.acquire('com1')
        pm.release('COM1')  # Different case
        
        # Original should still be in use
        assert pm.is_in_use('com1') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
