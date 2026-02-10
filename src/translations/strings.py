"""
Unified translation strings dictionary.
Format: key -> {language -> translation}
"""

from __future__ import annotations
from typing import Final

STRINGS: Final[dict[str, dict[str, str]]] = {
    # Common
    "app_name": {
        "ru": "UART Control",
        "en": "UART Control",
    },
    "loading": {
        "ru": "Загрузка...",
        "en": "Loading...",
    },
    "loading_initializing": {
        "ru": "Инициализация приложения...",
        "en": "Initializing application...",
    },
    "loading_theme_manager": {
        "ru": "Загрузка менеджера тем...",
        "en": "Loading theme manager...",
    },
    "loading_translator": {
        "ru": "Загрузка переводов...",
        "en": "Loading translator...",
    },
    "loading_models": {
        "ru": "Инициализация моделей...",
        "en": "Initializing models...",
    },
    "loading_ui": {
        "ru": "Сборка интерфейса...",
        "en": "Building user interface...",
    },
    "loading_styles": {
        "ru": "Применение стилей...",
        "en": "Applying styles...",
    },
    "loading_almost_ready": {
        "ru": "Почти готово...",
        "en": "Almost ready...",
    },
    "error": {
        "ru": "Ошибка",
        "en": "Error",
    },
    "success": {
        "ru": "Успешно",
        "en": "Success",
    },
    "cancel": {
        "ru": "Отмена",
        "en": "Cancel",
    },
    "save": {
        "ru": "Сохранить",
        "en": "Save",
    },
    "delete": {
        "ru": "Удалить",
        "en": "Delete",
    },
    "edit": {
        "ru": "Редактировать",
        "en": "Edit",
    },
    "add": {
        "ru": "Добавить",
        "en": "Add",
    },
    "close": {
        "ru": "Закрыть",
        "en": "Close",
    },
    "open": {
        "ru": "Открыть",
        "en": "Open",
    },
    "settings": {
        "ru": "Настройки",
        "en": "Settings",
    },
    "help": {
        "ru": "Помощь",
        "en": "Help",
    },
    "about": {
        "ru": "О программе",
        "en": "About",
    },
    
    # COM ports
    "com_port": {
        "ru": "COM Порт",
        "en": "COM Port",
    },
    "port_settings": {
        "ru": "Настройки порта",
        "en": "Port Settings",
    },
    "port_configuration": {
        "ru": "Конфигурация порта",
        "en": "Port Configuration",
    },
    "port_name": {
        "ru": "Имя порта",
        "en": "Port Name",
    },
    "baud_rate": {
        "ru": "Скорость",
        "en": "Baud Rate",
    },
    "data_bits": {
        "ru": "Биты данных",
        "en": "Data Bits",
    },
    "parity": {
        "ru": "Четность",
        "en": "Parity",
    },
    "stop_bits": {
        "ru": "Стоповые биты",
        "en": "Stop Bits",
    },
    "open_port": {
        "ru": "Открыть порт",
        "en": "Open Port",
    },
    "close_port": {
        "ru": "Закрыть порт",
        "en": "Close Port",
    },
    "port_status": {
        "ru": "Статус порта",
        "en": "Port Status",
    },
    "connected": {
        "ru": "Подключен",
        "en": "Connected",
    },
    "disconnected": {
        "ru": "Отключен",
        "en": "Disconnected",
    },
    
    # Data transmission
    "data_transmission": {
        "ru": "Передача данных",
        "en": "Data Transmission",
    },
    "send_data": {
        "ru": "Отправить данные",
        "en": "Send Data",
    },
    "received_data": {
        "ru": "Полученные данные",
        "en": "Received Data",
    },
    "send": {
        "ru": "Отправить",
        "en": "Send",
    },
    "send_to_cpu1": {
        "ru": "CPU1",
        "en": "CPU1",
    },
    "send_to_cpu2": {
        "ru": "CPU2",
        "en": "CPU2",
    },
    "send_to_both": {
        "ru": "1+2",
        "en": "1+2",
    },
    "combined": {
        "ru": "1+2",
        "en": "1+2",
    },
    "aux": {
        "ru": "AUX",
        "en": "AUX",
    },
    "clear": {
        "ru": "Очистить",
        "en": "Clear",
    },
    "hex_view": {
        "ru": "Шестнадцатеричный вид",
        "en": "Hex View",
    },
    "ascii_view": {
        "ru": "ASCII вид",
        "en": "ASCII View",
    },
    
    # Themes
    "theme": {
        "ru": "Тема",
        "en": "Theme",
    },
    "light_theme": {
        "ru": "Светлая",
        "en": "Light",
    },
    "dark_theme": {
        "ru": "Темная",
        "en": "Dark",
    },
    "system_theme": {
        "ru": "Системная",
        "en": "System",
    },
    
    # Language
    "language": {
        "ru": "Язык",
        "en": "Language",
    },
    "russian": {
        "ru": "Русский",
        "en": "Russian",
    },
    "english": {
        "ru": "Английский",
        "en": "English",
    },
    
    # Menu
    "file": {
        "ru": "Файл",
        "en": "File",
    },
    "edit": {
        "ru": "Правка",
        "en": "Edit",
    },
    "view": {
        "ru": "Вид",
        "en": "View",
    },
    "tools": {
        "ru": "Инструменты",
        "en": "Tools",
    },
    "window": {
        "ru": "Окно",
        "en": "Window",
    },
    "help_menu": {
        "ru": "Справка",
        "en": "Help",
    },
    
    # Status
    "ready": {
        "ru": "Готов",
        "en": "Ready",
    },
    "connecting": {
        "ru": "Подключение...",
        "en": "Connecting...",
    },
    "connected_to": {
        "ru": "Подключен к",
        "en": "Connected to",
    },
    "disconnected_from": {
        "ru": "Отключен от",
        "en": "Disconnected from",
    },
    "error_occurred": {
        "ru": "Произошла ошибка",
        "en": "Error occurred",
    },
    "port_not_found": {
        "ru": "Порт не найден",
        "en": "Port not found",
    },
    "port_already_open": {
        "ru": "Порт уже открыт",
        "en": "Port already open",
    },
    "port_already_closed": {
        "ru": "Порт уже закрыт",
        "en": "Port already closed",
    },
    
    # Settings
    "preferences": {
        "ru": "Предпочтения",
        "en": "Preferences",
    },
    "general_settings": {
        "ru": "Общие настройки",
        "en": "General Settings",
    },
    "port_settings_title": {
        "ru": "Настройки порта",
        "en": "Port Settings",
    },
    "data_format": {
        "ru": "Формат данных",
        "en": "Data Format",
    },
    "auto_connect": {
        "ru": "Автоподключение",
        "en": "Auto Connect",
    },
    "auto_reconnect": {
        "ru": "Автопереподключение",
        "en": "Auto Reconnect",
    },
    "buffer_size": {
        "ru": "Размер буфера",
        "en": "Buffer Size",
    },
    "timeout": {
        "ru": "Таймаут",
        "en": "Timeout",
    },
    
    # About
    "about_title": {
        "ru": "О программе",
        "en": "About",
    },
    "version": {
        "ru": "Версия",
        "en": "Version",
    },
    "author": {
        "ru": "Автор",
        "en": "Author",
    },
    "description": {
        "ru": "Современное приложение для управления COM портами",
        "en": "Modern COM port control application",
    },
    "license": {
        "ru": "Лицензия",
        "en": "License",
    },
    
    # Action buttons
    "start": {
        "ru": "Старт",
        "en": "Start",
    },
    "stop": {
        "ru": "Стоп",
        "en": "Stop",
    },
    "pause": {
        "ru": "Пауза",
        "en": "Pause",
    },
    "resume": {
        "ru": "Продолжить",
        "en": "Resume",
    },
    "apply": {
        "ru": "Применить",
        "en": "Apply",
    },
    "reset": {
        "ru": "Сброс",
        "en": "Reset",
    },
    "refresh": {
        "ru": "Обновить",
        "en": "Refresh",
    },
    "export": {
        "ru": "Экспорт",
        "en": "Export",
    },
    "import": {
        "ru": "Импорт",
        "en": "Import",
    },
    
    # Messages
    "no_ports_available": {
        "ru": "Доступные COM порты не найдены",
        "en": "No COM ports available",
    },
    "select_port": {
        "ru": "Выберите COM порт",
        "en": "Select COM port",
    },
    "invalid_baud_rate": {
        "ru": "Неверная скорость передачи",
        "en": "Invalid baud rate",
    },
    "invalid_data_format": {
        "ru": "Неверный формат данных",
        "en": "Invalid data format",
    },
    "connection_successful": {
        "ru": "Подключение установлено успешно",
        "en": "Connection established successfully",
    },
    "connection_failed": {
        "ru": "Не удалось установить подключение",
        "en": "Failed to establish connection",
    },
    "data_sent": {
        "ru": "Данные отправлены",
        "en": "Data sent",
    },
    "data_received": {
        "ru": "Данные получены",
        "en": "Data received",
    },
    "port_closed": {
        "ru": "Порт закрыт",
        "en": "Port closed",
    },
    
    # Context menu
    "copy": {
        "ru": "Копировать",
        "en": "Copy",
    },
    "paste": {
        "ru": "Вставить",
        "en": "Paste",
    },
    "cut": {
        "ru": "Вырезать",
        "en": "Cut",
    },
    "select_all": {
        "ru": "Выделить все",
        "en": "Select All",
    },
    "find": {
        "ru": "Найти",
        "en": "Find",
    },
    "replace": {
        "ru": "Заменить",
        "en": "Replace",
    },
    
    # Dialogs
    "confirm": {
        "ru": "Подтвердить",
        "en": "Confirm",
    },
    "warning": {
        "ru": "Предупреждение",
        "en": "Warning",
    },
    "information": {
        "ru": "Информация",
        "en": "Information",
    },
    "yes": {
        "ru": "Да",
        "en": "Yes",
    },
    "no": {
        "ru": "Нет",
        "en": "No",
    },
    "ok": {
        "ru": "ОК",
        "en": "OK",
    },
    
    # Logging
    "log": {
        "ru": "Лог",
        "en": "Log",
    },
    "clear_log": {
        "ru": "Очистить лог",
        "en": "Clear Log",
    },
    "save_log": {
        "ru": "Сохранить лог",
        "en": "Save Log",
    },
    "log_level": {
        "ru": "Уровень логирования",
        "en": "Log Level",
    },
    "debug": {
        "ru": "Отладка",
        "en": "Debug",
    },
    "info": {
        "ru": "Информация",
        "en": "Info",
    },
    "critical": {
        "ru": "Критический",
        "en": "Critical",
    },
    
    # Monitoring
    "monitor": {
        "ru": "Мониторинг",
        "en": "Monitor",
    },
    "start_monitoring": {
        "ru": "Начать мониторинг",
        "en": "Start Monitoring",
    },
    "stop_monitoring": {
        "ru": "Остановить мониторинг",
        "en": "Stop Monitoring",
    },
    "monitoring_active": {
        "ru": "Мониторинг активен",
        "en": "Monitoring Active",
    },
    "monitoring_stopped": {
        "ru": "Мониторинг остановлен",
        "en": "Monitoring Stopped",
    },
    
    # Filters
    "filter": {
        "ru": "Фильтр",
        "en": "Filter",
    },
    "apply_filter": {
        "ru": "Применить фильтр",
        "en": "Apply Filter",
    },
    "clear_filter": {
        "ru": "Очистить фильтр",
        "en": "Clear Filter",
    },
    "filter_by": {
        "ru": "Фильтровать по",
        "en": "Filter by",
    },
    
    # Profiles
    "profiles": {
        "ru": "Профили",
        "en": "Profiles",
    },
    "create_profile": {
        "ru": "Создать профиль",
        "en": "Create Profile",
    },
    "edit_profile": {
        "ru": "Редактировать профиль",
        "en": "Edit Profile",
    },
    "delete_profile": {
        "ru": "Удалить профиль",
        "en": "Delete Profile",
    },
    "load_profile": {
        "ru": "Загрузить профиль",
        "en": "Load Profile",
    },
    "save_profile": {
        "ru": "Сохранить профиль",
        "en": "Save Profile",
    },
    "profile_name": {
        "ru": "Имя профиля",
        "en": "Profile Name",
    },
}
