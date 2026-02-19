import os
from PySide6.QtCore import QObject, Signal

class Translator(QObject):
    """Class for managing application translations"""
    
    language_changed = Signal(str)  # Signal on language change
    
    def __init__(self, default_language: str = "ru_RU"):
        super().__init__()
        self.current_language = default_language
        # Language in code: ru or en
        self.current_lang_code = "en"
        self.translations = {}
        self.available_languages = {
            "ru_RU": "Русский",
            "en_US": "English"
        }
        self.load_translations()
    
    def load_translations(self):
        """Load translations for current language"""
        try:
            from src.translations.strings import STRINGS
            
            # Determine language code
            lang_code = "ru" if self.current_language == "ru_RU" else "en"
            self.current_lang_code = lang_code
            
            # Convert format: STRINGS["key"]["lang"] -> translations["key"]
            self.translations = {}
            for key, translations_dict in STRINGS.items():
                if isinstance(translations_dict, dict) and lang_code in translations_dict:
                    self.translations[key] = translations_dict[lang_code]
                    
        except ImportError:
            self.translations = {}
    
    def set_language(self, language: str):
        """Set current language"""
        if language in self.available_languages:
            self.current_language = language
            self.load_translations()
            self.language_changed.emit(language)
            return True
        return False
    
    def get_language(self) -> str:
        """Get current language"""
        return self.current_language
    
    def get_available_languages(self) -> dict[str, str]:
        """Get list of available languages"""
        return self.available_languages
    
    def translate(self, key: str, default: str | None = None) -> str:
        """Translate text by key"""
        if key in self.translations:
            return self.translations[key]
        elif default:
            return default
        else:
            return key
    
    def tr(self, key: str, default: str | None = None) -> str:
        """Alias for translate method"""
        return self.translate(key, default)

# Global translator instance
translator = Translator()

# Function for convenient access to translations with f-string style support
def tr(key: str, template: str, **kwargs) -> str:
    """Global function for translating text with variable substitution
    
    Args:
        key: Translation key
        template: Default template (used if translation not found)
        **kwargs: Variables for substitution in template
    
    Returns:
        Translated text with substituted variables
    """
    result = translator.translate(key, template)
    # If there are variables for substitution, perform replacement
    if kwargs:
        try:
            result = result.format(**kwargs)
        except (KeyError, ValueError):
            # If substitution failed, return as is
            pass
    return result
