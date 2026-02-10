import os
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal

class Translator(QObject):
    """Класс для управления переводами приложения"""
    
    language_changed = Signal(str)  # Сигнал при изменении языка
    
    def __init__(self, default_language: str = "ru_RU"):
        super().__init__()
        self.current_language = default_language
        # Язык в коде: ru или en
        self.current_lang_code = "ru"
        self.translations = {}
        self.available_languages = {
            "ru_RU": "Русский",
            "en_US": "English"
        }
        self.load_translations()
    
    def load_translations(self):
        """Загрузка переводов для текущего языка"""
        try:
            from src.translations.strings import STRINGS
            
            # Определяем код языка
            lang_code = "ru" if self.current_language == "ru_RU" else "en"
            self.current_lang_code = lang_code
            
            # Преобразуем формат: STRINGS["key"]["lang"] -> translations["key"]
            self.translations = {}
            for key, translations_dict in STRINGS.items():
                if isinstance(translations_dict, dict) and lang_code in translations_dict:
                    self.translations[key] = translations_dict[lang_code]
                    
        except ImportError:
            self.translations = {}
    
    def set_language(self, language: str):
        """Установка текущего языка"""
        if language in self.available_languages:
            self.current_language = language
            self.load_translations()
            self.language_changed.emit(language)
            return True
        return False
    
    def get_language(self) -> str:
        """Получение текущего языка"""
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """Получение списка доступных языков"""
        return self.available_languages
    
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """Перевод текста по ключу"""
        if key in self.translations:
            return self.translations[key]
        elif default:
            return default
        else:
            return key
    
    def tr(self, key: str, default: Optional[str] = None) -> str:
        """Алиас для метода translate"""
        return self.translate(key, default)

# Глобальный экземпляр переводчика
translator = Translator()

# Функция для удобного доступа к переводам
def tr(key: str, default: Optional[str] = None) -> str:
    """Глобальная функция для перевода текста"""
    return translator.translate(key, default)
