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
    "splash_title": {
        "ru": "UART Control",
        "en": "UART Control",
    },
    "splash_subtitle": {
        "ru": "Современное управление COM-портами",
        "en": "Modern COM Port Control",
    },
    "splash_logo_text": {
        "ru": "UART",
        "en": "UART",
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
    "ports_found": {
        "ru": "Найдено {count} порт(ов)",
        "en": "Found {count} port(s)",
    },
    "rx_label": {
        "ru": "RX: {count}",
        "en": "RX: {count}",
    },
    "tx_label": {
        "ru": "TX: {count}",
        "en": "TX: {count}",
    },
    "error_with_message": {
        "ru": "Ошибка: {message}",
        "en": "Error: {message}",
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
    "save_command": {
        "ru": "Сохранить команду",
        "en": "Save Command",
    },
    "command_history": {
        "ru": "История команд",
        "en": "Command History",
    },
    "clear_history": {
        "ru": "Очистить историю",
        "en": "Clear History",
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
    "tlm": {
        "ru": "TLM",
        "en": "TLM",
    },
    "send_to_tlm": {
        "ru": "Отправить в TLM",
        "en": "Send to TLM",
    },
    "tlm_log": {
        "ru": "Логи TLM",
        "en": "TLM Logs",
    },
    "send_to_all_three": {
        "ru": "1+2",
        "en": "All",
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

    # Status panels
    "port_counters": {
        "ru": "Счётчики портов",
        "en": "Port Counters",
    },
    "status": {
        "ru": "Статусы",
        "en": "Status",
    },
    "cpu1": {
        "ru": "CPU1",
        "en": "CPU1",
    },
    "cpu2": {
        "ru": "CPU2",
        "en": "CPU2",
    },
    "tlm": {
        "ru": "TLM",
        "en": "TLM",
    },
    "overall": {
        "ru": "Общее",
        "en": "Overall",
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
    "status_theme_changed": {
        "ru": "Тема: {theme}",
        "en": "Theme: {theme}",
    },
    "status_port_message": {
        "ru": "{port}: {message}",
        "en": "{port}: {message}",
    },
    "status_port_error": {
        "ru": "Ошибка ({port}): {message}",
        "en": "Error ({port}): {message}",
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

    # UI strings used in main window
    "port": {
        "ru": "Порт:",
        "en": "Port:",
    },
    "scan": {
        "ru": "Сканировать",
        "en": "Scan",
    },
    "scan_ports": {
        "ru": "Сканирование портов",
        "en": "Scan Ports",
    },
    "connect": {
        "ru": "Подключить",
        "en": "Connect",
    },
    "disconnect": {
        "ru": "Отключить",
        "en": "Disconnect",
    },
    "disconnecting": {
        "ru": "Отключение...",
        "en": "Disconnecting...",
    },
    "enter_command": {
        "ru": "Введите команду...",
        "en": "Enter command...",
    },
    "save_logs": {
        "ru": "Сохранить логи",
        "en": "Save Logs",
    },
    "logs_saved": {
        "ru": "Логи сохранены:",
        "en": "Logs saved to:",
    },
    "failed_save": {
        "ru": "Не удалось сохранить логи",
        "en": "Failed to save logs",
    },
    "search": {
        "ru": "Поиск",
        "en": "Search",
    },
    "search_logs": {
        "ru": "Поиск в логах...",
        "en": "Search logs...",
    },
    "show": {
        "ru": "Показать:",
        "en": "Show:",
    },
    "time": {
        "ru": "Время",
        "en": "Time",
    },
    "source": {
        "ru": "Источник",
        "en": "Source",
    },

    # Logging helpers
    "save_logs_prompt": {
        "ru": "Сохранить как:\n1. Один файл (все консоли вместе)\n2. Отдельные файлы для каждой консоли",
        "en": "Save as:\n1. Single file (all consoles)\n2. Separate files for each console",
    },
    "logs_combined_title": {
        "ru": "=== {app_name} - объединённые логи ===",
        "en": "=== {app_name} - Combined Logs ===",
    },
    "logs_generated": {
        "ru": "Сгенерировано: {timestamp}",
        "en": "Generated: {timestamp}",
    },
    "logs_section_cpu1": {
        "ru": "=== CPU1 ===",
        "en": "=== CPU1 ===",
    },
    "logs_section_cpu2": {
        "ru": "=== CPU2 ===",
        "en": "=== CPU2 ===",
    },
    "logs_section_tlm": {
        "ru": "=== TLM (Телеметрия) ===",
        "en": "=== TLM (Telemetry) ===",
    },
    "logs_saved_files": {
        "ru": "Сохранено {count} файл(ов):\n{files}",
        "en": "Saved {count} file(s):\n{files}",
    },

    # Serial worker
    "worker_connecting_to": {
        "ru": "Подключение к {port}...",
        "en": "Connecting to {port}...",
    },
    "worker_connected_to": {
        "ru": "Подключено к {port}",
        "en": "Connected to {port}",
    },
    "worker_disconnected_from": {
        "ru": "Отключено от {port}",
        "en": "Disconnected from {port}",
    },
    "worker_open_error": {
        "ru": "Ошибка открытия ({port}): {error}",
        "en": "Open error ({port}): {error}",
    },
    "worker_read_error": {
        "ru": "Ошибка чтения: {error}",
        "en": "Read error: {error}",
    },
    "worker_write_error": {
        "ru": "Ошибка записи ({port}): {error}",
        "en": "Write error ({port}): {error}",
    },
    "worker_tx_message": {
        "ru": "TX: {data}",
        "en": "TX: {data}",
    },
    "worker_simulated_echo": {
        "ru": "(симулируемый отклик) {data}",
        "en": "(simulated echo) {data}",
    },

    # COM ports manager
    "manager_port_already_connected": {
        "ru": "Порт уже подключен",
        "en": "Port already connected",
    },
    "manager_port_not_connected": {
        "ru": "Порт не подключен",
        "en": "Port not connected",
    },
    "manager_failed_connect": {
        "ru": "Не удалось подключиться к {port}: {error}",
        "en": "Failed to connect to {port}: {error}",
    },
    "manager_failed_disconnect": {
        "ru": "Не удалось отключиться от {port}: {error}",
        "en": "Failed to disconnect from {port}: {error}",
    },
    "manager_failed_send": {
        "ru": "Не удалось отправить данные на {port}: {error}",
        "en": "Failed to send data to {port}: {error}",
    },
    "manager_monitor_error": {
        "ru": "Ошибка мониторинга {port}: {error}",
        "en": "Error monitoring {port}: {error}",
    },
}
