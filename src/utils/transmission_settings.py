import json
import os
from typing import Dict

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'config', 'transmission_settings.json')

def _ensure_config_dir(path: str):
    dirpath = os.path.dirname(path)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

def load_settings() -> Dict:
    """Load transmission settings from JSON file."""
    # fallback path inside project config
    project_root = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(project_root, 'config', 'transmission_settings.json')
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
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
    project_root = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(project_root, 'config', 'transmission_settings.json')
    try:
        _ensure_config_dir(cfg_path)
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
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
    except Exception:
        return False

def clear_history():
    try:
        settings = load_settings()
        settings['history'] = []
        save_settings(settings)
        return True
    except Exception:
        return False
