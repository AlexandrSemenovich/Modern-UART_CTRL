import json
import logging
from typing import Dict

from src.utils.paths import get_config_file, ensure_dir

_logger = logging.getLogger(__name__)

def load_settings() -> Dict:
    """Load transmission settings from JSON file."""
    cfg_path = get_config_file("transmission_settings.json")
    try:
        if cfg_path.exists():
            with cfg_path.open('r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as exc:  # pragma: no cover - защита на случай повреждённого файла
        _logger.warning("Failed to load transmission settings from %s: %s", cfg_path, exc)
    # defaults
    return {
        'autoscroll': True,
        'show_timestamps': False,
        'append_newline': False,
        'send_format': 'text',
        'history': []
    }

def save_settings(settings: Dict):
    """Save transmission settings to JSON file."""
    cfg_path = get_config_file("transmission_settings.json")
    try:
        ensure_dir(cfg_path)
        with cfg_path.open('w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:  # pragma: no cover
        _logger.error("Failed to save transmission settings to %s: %s", cfg_path, exc)
        return False

def add_history_entry(entry: str, max_items: int = 50):
    try:
        settings = load_settings()
        history = settings.get('history', []) or []
        if entry in history:
            history.remove(entry)
        history.insert(0, entry)
        history = history[:max_items]
        settings['history'] = history
        save_settings(settings)
        return True
    except Exception as exc:  # pragma: no cover
        _logger.error("Failed to add history entry to transmission settings: %s", exc)
        return False

def clear_history():
    try:
        settings = load_settings()
        settings['history'] = []
        save_settings(settings)
        return True
    except Exception as exc:  # pragma: no cover
        _logger.error("Failed to clear transmission history: %s", exc)
        return False
