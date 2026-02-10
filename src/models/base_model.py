from PySide6.QtCore import QObject, Signal, Property

class BaseModel(QObject):
    """Базовый класс для всех моделей в MVVM"""
    
    loading_changed = Signal()
    error_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._is_loading = False
        self._error_message = ""
    
    def set_loading(self, loading):
        """Установка состояния загрузки"""
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_changed.emit()
    
    def set_error(self, message):
        """Установка сообщения об ошибке"""
        if self._error_message != message:
            self._error_message = message
            self.error_changed.emit()
    
    @Property(bool, notify=loading_changed)
    def is_loading(self):
        return self._is_loading
    
    @Property(str, notify=error_changed)
    def error_message(self):
        return self._error_message