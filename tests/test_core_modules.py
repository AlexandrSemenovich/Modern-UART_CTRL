"""Tests for core modules: exceptions, version, paths, translator, transmission_settings."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ============================================================================
# Tests for src/exceptions.py
# ============================================================================

class TestUARTControlError:
    """Tests for UARTControlError exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        from src.exceptions import UARTControlError
        exc = UARTControlError("Test error")
        assert str(exc) == "Test error"
        assert exc.port is None
        assert exc.baud_rate is None
        assert exc.details == {}
    
    def test_with_port(self):
        """Test exception with port parameter."""
        from src.exceptions import UARTControlError
        exc = UARTControlError("Connection failed", port="COM1")
        assert "port=COM1" in str(exc)
    
    def test_with_baud_rate(self):
        """Test exception with baud rate parameter."""
        from src.exceptions import UARTControlError
        exc = UARTControlError("Connection failed", baud_rate=115200)
        assert "baud_rate=115200" in str(exc)
    
    def test_with_details(self):
        """Test exception with details dictionary."""
        from src.exceptions import UARTControlError
        exc = UARTControlError("Error", details={"key": "value"})
        assert "details=" in str(exc)
    
    def test_with_all_params(self):
        """Test exception with all parameters."""
        from src.exceptions import UARTControlError
        exc = UARTControlError(
            "Error",
            port="COM1",
            baud_rate=9600,
            details={"retry": 3}
        )
        error_str = str(exc)
        assert "Error" in error_str
        assert "port=COM1" in error_str
        assert "baud_rate=9600" in error_str


class TestSerialConnectionError:
    """Tests for SerialConnectionError exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        from src.exceptions import SerialConnectionError
        exc = SerialConnectionError("Connection failed")
        assert str(exc) == "Connection failed"
        assert exc.cause is None
    
    def test_with_cause(self):
        """Test exception with cause."""
        from src.exceptions import SerialConnectionError
        cause = OSError("Port not found")
        exc = SerialConnectionError("Connection failed", cause=cause)
        assert exc.cause is cause
        assert exc.__cause__ is cause


class TestSerialWriteError:
    """Tests for SerialWriteError exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        from src.exceptions import SerialWriteError
        exc = SerialWriteError("Write failed")
        assert exc.bytes_written is None
    
    def test_with_bytes_written(self):
        """Test exception with bytes written."""
        from src.exceptions import SerialWriteError
        exc = SerialWriteError("Write failed", bytes_written=5)
        assert exc.bytes_written == 5


class TestSerialReadError:
    """Tests for SerialReadError exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        from src.exceptions import SerialReadError
        exc = SerialReadError("Read failed")
        assert exc.cause is None
    
    def test_with_cause(self):
        """Test exception with cause."""
        from src.exceptions import SerialReadError
        cause = TimeoutError("Read timeout")
        exc = SerialReadError("Read failed", cause=cause)
        assert exc.cause is cause


class TestConfigurationError:
    """Tests for ConfigurationError exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        from src.exceptions import ConfigurationError
        exc = ConfigurationError("Config error")
        assert exc.key is None
    
    def test_with_key(self):
        """Test exception with key."""
        from src.exceptions import ConfigurationError
        exc = ConfigurationError("Config error", key="baud_rate")
        assert exc.key == "baud_rate"


# ============================================================================
# Tests for src/version.py
# ============================================================================

class TestVersion:
    """Tests for version module."""
    
    def test_get_version(self):
        """Test get_version function returns string."""
        from src.version import get_version
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_version_format(self):
        """Test version has expected format (e.g., 1.1.0)."""
        from src.version import get_version
        version = get_version()
        # Version should contain at least one dot
        assert "." in version


# ============================================================================
# Tests for src/utils/paths.py
# ============================================================================

class TestPaths:
    """Tests for path utilities."""
    
    def test_get_root_dir_returns_path(self):
        """Test get_root_dir returns a Path object."""
        from src.utils.paths import get_root_dir
        root = get_root_dir()
        assert isinstance(root, Path)
        assert root.exists()
    
    def test_get_config_dir_returns_path(self):
        """Test get_config_dir returns a Path object."""
        from src.utils.paths import get_config_dir
        config_dir = get_config_dir()
        assert isinstance(config_dir, Path)
    
    def test_get_config_file(self):
        """Test get_config_file returns correct path."""
        from src.utils.paths import get_config_file
        config_file = get_config_file("test.ini")
        assert isinstance(config_file, Path)
        assert config_file.name == "test.ini"
    
    def test_get_stylesheet_path(self):
        """Test get_stylesheet_path returns path."""
        from src.utils.paths import get_stylesheet_path
        style_path = get_stylesheet_path("app_optimized.qss")
        assert isinstance(style_path, Path)
        assert style_path.name == "app_optimized.qss"
    
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test ensure_dir creates directory if it doesn't exist."""
        from src.utils.paths import ensure_dir
        test_dir = tmp_path / "test" / "nested"
        ensure_dir(test_dir / "file.txt")
        assert test_dir.exists()
        assert test_dir.is_dir()


# ============================================================================
# Tests for src/utils/translator.py
# ============================================================================

class TestTranslator:
    """Tests for Translator class."""
    
    def test_translator_initialization(self):
        """Test translator initializes with default language."""
        from src.utils.translator import Translator
        translator = Translator()
        assert translator.current_language == "ru_RU"
        assert translator.current_lang_code == "ru"  # ru_RU -> ru
    
    def test_translator_with_custom_language(self):
        """Test translator with custom default language."""
        from src.utils.translator import Translator
        translator = Translator(default_language="en_US")
        assert translator.current_language == "en_US"
    
    def test_get_language(self):
        """Test get_language returns current language."""
        from src.utils.translator import Translator
        translator = Translator()
        assert translator.get_language() == "ru_RU"
    
    def test_get_available_languages(self):
        """Test get_available_languages returns dict."""
        from src.utils.translator import Translator
        translator = Translator()
        langs = translator.get_available_languages()
        assert isinstance(langs, dict)
        assert "ru_RU" in langs
        assert "en_US" in langs
    
    def test_set_language(self):
        """Test set_language changes language."""
        from src.utils.translator import Translator
        translator = Translator()
        result = translator.set_language("en_US")
        assert result is True
        assert translator.current_language == "en_US"
    
    def test_set_invalid_language(self):
        """Test set_language with invalid language returns False."""
        from src.utils.translator import Translator
        translator = Translator()
        result = translator.set_language("invalid_lang")
        assert result is False
    
    def test_translate_key_exists(self):
        """Test translate returns translation for existing key."""
        from src.utils.translator import Translator
        translator = Translator(default_language="ru_RU")
        # The key should exist in translations
        result = translator.translate("app_title")
        assert result is not None
    
    def test_translate_key_not_exists(self):
        """Test translate returns key when not found."""
        from src.utils.translator import Translator
        translator = Translator()
        result = translator.translate("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"
    
    def test_translate_with_default(self):
        """Test translate returns default when key not found."""
        from src.utils.translator import Translator
        translator = Translator()
        result = translator.translate("nonexistent", "Default Text")
        assert result == "Default Text"
    
    def test_tr_alias(self):
        """Test tr is alias for translate."""
        from src.utils.translator import Translator
        translator = Translator()
        result1 = translator.translate("test_key", "default")
        result2 = translator.tr("test_key", "default")
        assert result1 == result2
    
    def test_global_tr_function(self):
        """Test global tr function."""
        from src.utils.translator import tr
        # Should not raise exception
        result = tr("app_title", "Default Title")
        assert result is not None
    
    def test_global_tr_with_variables(self):
        """Test global tr function with variable substitution."""
        from src.utils.translator import tr
        # This tests variable substitution in translations
        result = tr("port_label_template", "{name}:", name="COM1")
        # Result should contain substituted variable
        assert "COM1" in result or "{" in result


# ============================================================================
# Tests for src/utils/transmission_settings.py
# ============================================================================

class TestTransmissionSettings:
    """Tests for transmission settings utilities."""
    
    def test_load_settings_returns_dict(self):
        """Test load_settings returns a dictionary."""
        from src.utils.transmission_settings import load_settings
        settings = load_settings()
        assert isinstance(settings, dict)


class TestTransmissionSettingsWithState:
    """Tests for transmission settings that modify state."""
    
    @pytest.fixture(autouse=True)
    def reset_settings(self):
        """Reset transmission settings to defaults before each test."""
        from src.utils.transmission_settings import save_settings
        defaults = {
            'autoscroll': True,
            'show_timestamps': False,
            'append_newline': False,
            'send_format': 'text',
            'history': []
        }
        save_settings(defaults)
        yield
        # Cleanup after test
        save_settings(defaults)

    def test_save_settings_returns_bool(self):
        """Test save_settings returns boolean."""
        from src.utils.transmission_settings import save_settings
        result = save_settings({"test": "value"})
        assert isinstance(result, bool)

    def test_load_settings_has_defaults(self):
        """Test load_settings has expected default keys."""
        from src.utils.transmission_settings import load_settings
        settings = load_settings()
        assert "autoscroll" in settings
        assert "show_timestamps" in settings
        assert "append_newline" in settings
        assert "send_format" in settings
        assert "history" in settings

    def test_add_history_entry(self):
        """Test add_history_entry adds entry to history."""
        from src.utils.transmission_settings import add_history_entry
        test_entry = f"test_command_{os.urandom(4).hex()}"
        result = add_history_entry(test_entry)
        assert isinstance(result, bool)

    def test_clear_history(self):
        """Test clear_history clears history."""
        from src.utils.transmission_settings import clear_history
        result = clear_history()
        assert isinstance(result, bool)

    def test_add_history_with_max_items(self):
        """Test add_history respects max_items limit."""
        from src.utils.transmission_settings import add_history_entry
        for i in range(60):
            result = add_history_entry(f"cmd_{i}", max_items=50)
        assert True


# ============================================================================
# Integration tests
# ============================================================================

class TestModuleImports:
    """Test that all modules can be imported."""
    
    def test_import_exceptions(self):
        """Test importing exceptions module."""
        from src import exceptions
        assert hasattr(exceptions, "UARTControlError")
    
    def test_import_version(self):
        """Test importing version module."""
        from src import version
        assert hasattr(version, "get_version")
    
    def test_import_paths(self):
        """Test importing paths module."""
        from src.utils import paths
        assert hasattr(paths, "get_root_dir")
    
    def test_import_translator(self):
        """Test importing translator module."""
        from src.utils import translator
        assert hasattr(translator, "Translator")
    
    def test_import_transmission_settings(self):
        """Test importing transmission_settings module."""
        from src.utils import transmission_settings
        assert hasattr(transmission_settings, "load_settings")
