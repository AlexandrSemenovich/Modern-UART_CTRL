"""
Pytest configuration and fixtures for testing.
Provides common fixtures for Qt and serial port testing.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def tmp_path(tmp_path_factory):
    """
    Override tmp_path fixture to use project temp directory.
    This works around permission issues with Windows temp directory.
    """
    import shutil
    project_root = Path(__file__).parent.parent
    temp_dir = project_root / "temp_test_files"
    temp_dir.mkdir(exist_ok=True)
    
    # Create a unique temp directory inside our temp folder
    import uuid
    unique_dir = temp_dir / f"test_{uuid.uuid4().hex}"
    unique_dir.mkdir(exist_ok=True)
    return unique_dir


@pytest.fixture(scope='session')
def qapp():
    """
    Create QApplication instance for Qt tests.
    This is a session-scoped fixture that provides a single QApplication
    for all tests in the session.
    """
    from PySide6 import QtWidgets
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    yield app
    # Don't quit the app here as it may be needed by other tests


@pytest.fixture
def mock_serial(monkeypatch):
    """
    Mock pyserial module for testing without actual serial ports.
    """
    from unittest.mock import MagicMock
    
    mock = MagicMock()
    mock.Serial = MagicMock()
    mock.SerialException = Exception
    monkeypatch.setitem(sys.modules, 'serial', mock)
    return mock


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Create a temporary config file for testing.
    """
    config_content = """[colors.dark]
timestamp = #aaaaaa
rx_text = #c7f0c0
rx_label = #4caf50
tx_text = #fff7d6
tx_label = #ffdd57
sys_text = #cccccc
sys_label = #bbbbbb

[colors.light]
timestamp = #666666
rx_text = #2b6d2b
rx_label = #1f7a1f
tx_text = #a06b00
tx_label = #c78a00
sys_text = #666666
sys_label = #888888

[serial]
default_read_interval = 0.02
connection_timeout = 5.0
connection_retry_delay = 0.5
max_connection_attempts = 3
max_consecutive_errors = 3

[console]
max_html_length = 10000
max_document_lines = 1000
trim_chunk_size = 500
max_cache_lines = 10000

[fonts]
default_family = Segoe UI
default_size = 10
title_size = 14
button_size = 10
monospace_family = Courier New
monospace_size = 9
"""
    config_file = tmp_path / "test_config.ini"
    config_file.write_text(config_content, encoding='utf-8')
    return config_file


@pytest.fixture
def reset_port_manager():
    """
    Reset the PortManager singleton between tests.
    """
    from src.utils.port_manager import port_manager
    port_manager.clear()
    yield
    port_manager.clear()


@pytest.fixture
def sample_serial_config():
    """
    Sample serial configuration for testing.
    """
    return {
        'port': 'COM1',
        'baud': 115200,
        'timeout': 0.1,
        'charset': 'utf-8',
    }
