"""
English translations module (generated from strings.py)
Provides `TRANSLATIONS` mapping for tests that expect language-specific modules.
"""
from .strings import STRINGS

TRANSLATIONS = {k: v.get('en', '') for k, v in STRINGS.items()}
