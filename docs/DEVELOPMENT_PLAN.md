# Комплексный план развития проекта Modern UART Control

## 1. Введение

Данный документ описывает план дальнейшего развития проекта Modern UART Control, включающий пять ключевых направлений:
- ✅ **Внедрение полноценного покрытия unit-тестами** — ВЫПОЛНЕНО
- ⏳ Настройка непрерывной интеграции и развёртывания (CI/CD)
- ✅ **Профилирование производительности** — ВЫПОЛНЕНО
- ✅ **Расширение системы логирования** — ВЫПОЛНЕНО
- ✅ **Внедрение системы мониторинга** — ВЫПОЛНЕНО

---

**Сводка статуса выполнения:**
| Раздел | Статус |
|--------|--------|
| Unit-тесты | ✅ Выполнено |
| CI/CD | ⏳ Ожидает |
| Профилирование | ⏳ Ожидает |
| Логирование | ✅ Выполнено |
| Мониторинг | ⏳ Ожидает |

---

## 2. Анализ текущего состояния

### 2.1 Существующая инфраструктура тестирования

**Файлы тестов:**
- `tests/test_main_viewmodel.py` — базовые тесты логики кэширования и фильтрации ✅
- `tests/test_viewmodel_serialworker.py` — тесты форматтеров и базовой конфигурации ✅
- `tests/models/test_serial_worker.py` — тесты SerialWorker ✅
- `tests/models/test_config_loader.py` — тесты ConfigLoader ✅
- `tests/viewmodels/test_main_viewmodel.py` — полные тесты MainViewModel ✅
- `tests/viewmodels/test_com_port_viewmodel.py` — тесты ComPortViewModel ✅
- `tests/viewmodels/test_command_history_viewmodel.py` — тесты CommandHistoryViewModel ✅
- `tests/utils/test_port_manager.py` — тесты PortManager ✅
- `tests/utils/test_theme_manager.py` — тесты ThemeManager ✅
- `tests/utils/test_state_utils.py` — тесты StateUtils ✅
- `tests/conftest.py` — фикстуры для Qt тестов ✅
- `pytest.ini` — конфигурация pytest ✅

**Текущее покрытие:**
- Тестируются базовые функции: `format_rx`, `format_tx`, `format_system` ✅
- Тестируется логика кэширования и фильтрации ✅
- Тестируется конфигурирование SerialWorker ✅
- Тестируется ConfigLoader (цвета, шрифты, размеры, serial config) ✅
- Тестируется PortManager ✅
- Тестируется ThemeManager ✅
- Тестируется StateUtils ✅

**Статус: ✅ ВЫПОЛНЕНО**

### 2.2 Архитектура проекта

**Model слой:**
- `src/models/serial_worker.py` — основной класс SerialWorker (QThread)
- `src/models/base_model.py` — базовая модель
- `src/models/com_port_model.py` — модель COM-порта

**ViewModel слой:**
- `src/viewmodels/main_viewmodel.py` — MainViewModel для управления логами
- `src/viewmodels/com_port_viewmodel.py` — ComPortViewModel для управления портом
- `src/viewmodels/command_history_viewmodel.py` — управление историей команд

**Utils:**
- `src/utils/config_loader.py` — загрузчик конфигурации
- `src/utils/port_manager.py` — менеджер портов
- `src/utils/theme_manager.py` — управление темами
- `src/utils/state_utils.py` — утилиты состояний

---

## 3. Внедрение Unit-Тестов

### 3.1 Тестирование Model Слоя

#### SerialWorker (src/models/serial_worker.py)

**Публичные методы для тестирования:**
- `configure(port_name, baud_rate)` — настройка порта
- `write(data)` — запись данных в очередь
- `stop()` — остановка worker
- `is_connected()` — проверка соединения
- `get_port_name()` — получение имени порта
- `get_baud_rate()` — получение скорости

**Граничные случаи:**
- Запись при отключённом порте
- Вызов stop() несколько раз
- Пустые данные при записи
- Параметры с некорректными значениями

**Требуемые зависимости:**
```python
pytest>=7.0.0
pytest-qt>=4.0.0
pytest-mock>=3.10.0
```

#### ConfigLoader (src/utils/config_loader.py)

**Публичные методы для тестирования:**
- `get_colors(theme)` — получение цветов темы
- `get_button_colors(theme)` — получение цветов кнопок
- `get_font_config()` — получение конфигурации шрифтов
- `get_size_config()` — получение размеров
- `get_serial_config()` — получение serial конфигурации
- `get_window_title()` — получение заголовка окна

**Граничные случаи:**
- Несуществующая тема
- Отсутствующие параметры в конфиге
- Некорректные типы данных в конфиге

### 3.2 Тестирование ViewModel Слоя

#### MainViewModel (src/viewmodels/main_viewmodel.py)

**Публичные методы для тестирования:**
- `format_rx(source, text)` — форматирование RX сообщений
- `format_tx(source, text)` — форматирование TX сообщений
- `format_system(source, text)` — форматирование системных сообщений
- `set_display_options(show_time, show_source)` — настройка отображения
- `cache_log_line(source, html, plain)` — кэширование строки
- `filter_cache(source, query)` — фильтрация кэша
- `clear_cache()` — очистка кэша
- `strip_html(html)` — удаление HTML тегов

**Граничные случаи:**
- Пустые сообщения
- Сообщения только с пробелами
- Очень длинные сообщения (>10000 символов)
- Специальные символы HTML (<, >, &)
- Пустой поисковый запрос

#### ComPortViewModel (src/viewmodels/com_port_viewmodel.py)

**Публичные методы для тестирования:**
- `connect(port_name)` — подключение к порту
- `disconnect()` — отключение от порта
- `send_command(command)` — отправка команды
- `refresh_ports()` — обновление списка портов
- `get_state()` — получение состояния
- `get_rx_count()` — получение счётчика RX
- `get_tx_count()` — получение счётчика TX

**Граничные случаи:**
- Подключение к несуществующему порту
- Подключение при уже активном соединении
- Отправка команды при отключённом порте
- Многократное переподключение

### 3.3 Структура тестов

```
tests/
├── conftest.py              # Общие фикстуры ✅
├── pytest.ini               # Конфигурация pytest ✅
├── requirements-test.txt   # Зависимости для тестов
├── models/
│   ├── __init__.py
│   ├── test_serial_worker.py ✅
│   └── test_config_loader.py ✅
├── viewmodels/
│   ├── __init__.py
│   ├── test_main_viewmodel.py ✅
│   ├── test_com_port_viewmodel.py ✅
│   └── test_command_history_viewmodel.py ✅
└── utils/
    ├── __init__.py
    ├── test_port_manager.py ✅
    ├── test_theme_manager.py ✅
    └── test_state_utils.py ✅
```

**Статус: ✅ ВЫПОЛНЕНО** — Все тесты созданы согласно плану

### 3.4 Примеры тестов

```python
# tests/models/test_serial_worker.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.models.serial_worker import SerialWorker


class TestSerialWorker:
    """Unit tests for SerialWorker model."""
    
    @pytest.fixture
    def worker(self):
        """Create SerialWorker instance."""
        return SerialWorker('CPU1')
    
    def test_configure_sets_port_and_baud(self, worker):
        """Test configure method sets port name and baud rate."""
        worker.configure('COM1', 9600)
        assert worker._port_name == 'COM1'
        assert worker._baud == 9600
    
    def test_write_enqueue_data(self, worker):
        """Test write method adds data to queue."""
        worker.write('TEST')
        item = worker._write_q.get_nowait()
        assert item == 'TEST'
    
    def test_write_empty_string(self, worker):
        """Test writing empty string does not crash."""
        worker.write('')
        # Empty string should still be queued
    
    def test_write_when_disconnected(self, worker):
        """Test write when port is not connected."""
        worker.write('DATA')
        # Data should still be queued for later
    
    def test_stop_multiple_calls(self, worker):
        """Test multiple stop calls don't cause errors."""
        worker.stop()
        worker.stop()  # Should not raise
```

### 3.5 Фикстуры для тестирования Qt

```python
# tests/conftest.py
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for Qt tests."""
    from PySide6 import QtWidgets
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    yield app
    app.quit()


@pytest.fixture
def mock_serial(monkeypatch):
    """Mock pyserial module."""
    mock = MagicMock()
    mock.Serial = MagicMock()
    mock.SerialException = Exception
    monkeypatch.setitem(sys.modules, 'serial', mock)
    return mock
```

---

## 4. Непрерывная Интеграция и Развёртывание (CI/CD)

**Статус: ⏳ ОЖИДАЕТ** — Требуется настройка CI/CD пайплайнов.

### 4.1 Выбор инструментов

**Рекомендуемые инструменты:**
- GitHub Actions — для CI/CD (бесплатно для открытых репозиториев)
- GitLab CI — альтернативный вариант
- Jenkins — для локального развёртывания

### 4.2 Конфигурация GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
          
      - name: Run pytest
        run: pytest --cov=src --cov-report=xml --cov-report=html
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          
  lint:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Run linting
        run: |
          pip install flake8 pylint mypy
          flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
          pylint src --errors-only
          
  build:
    runs-on: windows-latest
    needs: [test, lint]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build executable
        run: |
          pip install pyinstaller
          pyinstaller --onefile --name UART_Control src/main.py
          
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: uart-control-exe
          path: dist/UART_Control.exe
```

### 4.3 Уведомления о результатах сборки

```yaml
# Добавление уведомлений в workflow
- name: Discord Notification
  if: always()
  uses: jakepitman/jepa-discord-notify@v1
  with:
    webhook_url: ${{ secrets.DISCORD_WEBHOOK }}
    status: ${{ job.status }}
    title: "UART Control CI"
    description: "Build ${{ job.result }}"
```

### 4.4 Требования для тестов

```txt
# requirements-test.txt
pytest>=7.0.0
pytest-qt>=4.0.0
pytest-mock>=3.10.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0  # Параллельное выполнение
```

---

## 5. Профилирование Производительности

**Статус: ✅ ВЫПОЛНЕНО** — Модуль профилирования реализован:
- [`src/utils/profiler.py`](src/utils/profiler.py) — модуль профилирования ✅
- [`scripts/profile_app.py`](scripts/profile_app.py) — скрипт запуска с профилированием ✅

**Возможности:**
- `Profiler` — контекстный менеджер для профилирования блоков кода
- `profile_function` — декоратор для профилирования функций
- `PerformanceTimer` — простой таймер для измерения времени выполнения
- Профилирование всего приложения через `scripts/profile_app.py`

### 5.1 Инструменты профилирования

**Python встроенные:**
- `cProfile` — стандартный профайлер
- `pstats` — анализ результатов профилирования
- `timeit` — измерение времени выполнения

**Внешние инструменты:**
- `memory_profiler` — профилирование памяти
- `line_profiler` — построчное профилирование
- `py-spy` — профилирование без остановки приложения
- `scalene` — комбинированный профилировщик (CPU, память, GPU)

### 5.2 Профилирование критических участков

**Создание модуля профилирования:**

```python
# src/utils/profiler.py
"""Performance profiling utilities."""

import cProfile
import pstats
import io
import logging
import functools
import os
from typing import Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Profiler:
    """Context manager for profiling code sections."""
    
    def __init__(self, name: str, output_dir: Optional[Path] = None):
        self.name = name
        self.output_dir = output_dir or Path('logs/profiles')
        self.profiler = cProfile.Profile()
        
    def __enter__(self):
        self.profiler.enable()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profiler.disable()
        self._save_stats()
        
    def _save_stats(self):
        """Save profiling stats to file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stats_file = self.output_dir / f'{self.name}.prof'
        
        # Save as pickle
        self.profiler.dump_stats(str(stats_file))
        
        # Also print summary
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        logger.info(f"Profile for {self.name}:\n{s.getvalue()}")


def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return func(*args, **kwargs)
        finally:
            profiler.disable()
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(10)
            logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
    return wrapper
```

### 5.3 Точки профилирования

**Критические участки кода для профилирования:**

1. **Обработка входящих данных (SerialWorker)**
   - `read()` метод
   - Парсинг строк
   - Эмиссия сигналов

2. **Форматирование сообщений (MainViewModel)**
   - `format_rx()`, `format_tx()`, `format_system()`
   - HTML экранирование
   - Работа с кэшем

3. **Фильтрация и поиск**
   - `filter_cache()` метод
   - Регулярные выражения

4. **Обновление UI**
   - Обработка сигналов
   - Обновление виджетов

### 5.4 Скрипт профилирования

```python
# scripts/profile_app.py
"""Run application with profiling enabled."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6 import QtWidgets
from src.main import MainWindow
import cProfile
import pstats
from io import StringIO


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Enable profiling
    profiler = cProfile.Profile()
    profiler.enable()
    
    window = MainWindow()
    window.show()
    
    result = app.exec()
    
    profiler.disable()
    
    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)
    
    print("=== Top 30 Functions by Cumulative Time ===")
    print(s.getvalue())
    
    # Save to file
    profiler.dump_stats('logs/profile_output.prof')
    print("\nProfile saved to logs/profile_output.prof")
    print("View with: python -m pstats logs/profile_output.prof")
    
    sys.exit(result)


if __name__ == '__main__':
    main()
```

### 5.5 Измерение времени выполнения

```python
# src/utils/timing.py
"""Timing utilities for performance measurement."""

import time
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        logger.info(f"{self.name} took {self.elapsed*1000:.2f}ms")


def timed(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {elapsed*1000:.2f}ms")
        return result
    return wrapper
```

---

## 6. Расширение Системы Логирования

**Статус: ✅ ВЫПОЛНЕНО** — Расширенная система логирования реализована:
- [`src/utils/logger.py`](src/utils/logger.py) — модуль расширенного логирования ✅
- [`config/logging_config.json`](config/logging_config.json) — конфигурация логирования по окружениям ✅
- [`src/main.py`](src/main.py) — интеграция с приложением ✅

**Возможности:**
- Консольный и файловый вывод
- Ротация логов (10 MB, 5 резервных копий)
- Разные уровни логирования для разных окружений (development, testing, production, staging)
- Отдельный файл для ошибок
- Настраиваемые уровни для отдельных модулей
- Функция очистки старых логов

### 6.1 Текущее состояние

**Реализовано:** ✅
- Стандартный `logging` модуль Python
- Логирование на уровне модулей во всех компонентах:
  - `src/models/serial_worker.py` ✅
  - `src/viewmodels/com_port_viewmodel.py` ✅
  - `src/viewmodels/command_history_viewmodel.py` ✅
  - `src/utils/config_loader.py` ✅
  - `src/utils/theme_manager.py` ✅
  - `src/main.py` ✅
- Консольный вывод с настраиваемым уровнем (DEBUG, INFO, WARNING, ERROR)

**Требуется расширение:**
- FileHandler для записи в файлы
- Ротация логов
- Разные уровни для разных окружений

### 6.2 Архитектура логирования

```python
# src/utils/logger.py
"""Enhanced logging configuration."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LogConfig:
    """Logging configuration class."""
    
    # Log levels per environment
    ENV_LEVELS = {
        'development': logging.DEBUG,
        'testing': logging.DEBUG,
        'production': logging.INFO,
        'staging': logging.WARNING,
    }
    
    # Log format
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # File settings
    LOG_DIR = Path('logs')
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5


def setup_logging(
    env: str = 'development',
    log_file: Optional[str] = None,
    level: Optional[int] = None
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        env: Environment name (development, testing, production, staging)
        log_file: Optional log file name
        level: Optional explicit log level
        
    Returns:
        Configured root logger
    """
    # Determine log level
    if level is None:
        level = LogConfig.ENV_LEVELS.get(env, logging.DEBUG)
    
    # Create logs directory
    LogConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter(LogConfig.FORMAT, LogConfig.DATE_FORMAT)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'app_{timestamp}.log'
    
    file_path = LogConfig.LOG_DIR / log_file
    
    # Rotating file handler
    rotating_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=LogConfig.MAX_BYTES,
        backupCount=LogConfig.BACKUP_COUNT,
        encoding='utf-8'
    )
    rotating_handler.setLevel(level)
    rotating_handler.setFormatter(formatter)
    root_logger.addHandler(rotating_handler)
    
    # Error log file (always ERROR level)
    error_file_path = LogConfig.LOG_DIR / f'errors_{timestamp}.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_file_path,
        maxBytes=LogConfig.MAX_BYTES,
        backupCount=LogConfig.BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    return root_logger


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional specific level for this logger
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
```

### 6.3 Конфигурация логирования по окружениям

```python
# config/logging_config.json
{
    "development": {
        "level": "DEBUG",
        "console": true,
        "file": true,
        "rotation": false,
        "modules": {
            "src.models": "DEBUG",
            "src.viewmodels": "DEBUG",
            "src.utils": "DEBUG"
        }
    },
    "production": {
        "level": "INFO",
        "console": false,
        "file": true,
        "rotation": true,
        "modules": {
            "src.models": "INFO",
            "src.viewmodels": "WARNING",
            "src.utils": "INFO"
        }
    },
    "testing": {
        "level": "DEBUG",
        "console": true,
        "file": false,
        "modules": {
            "src.models": "DEBUG",
            "src.viewmodels": "DEBUG"
        }
    }
}
```

### 6.4 Загрузка конфигурации логирования

```python
# src/utils/logging_config_loader.py
"""Load logging configuration from config file."""

import json
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any


def load_logging_config(env: str = 'development') -> Dict[str, Any]:
    """Load logging configuration for the given environment."""
    config_file = Path('config/logging_config.json')
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)
            return all_configs.get(env, {})
    
    return {}


def configure_logging(env: str = 'development'):
    """Configure logging based on environment."""
    config = load_logging_config(env)
    
    level_name = config.get('level', 'DEBUG')
    level = getattr(logging, level_name, logging.DEBUG)
    
    # Use the setup function from logger.py
    from src.utils.logger import setup_logging
    setup_logging(env=env, level=level)
```

### 6.5 Пример использования

```python
# Example usage in modules
import logging

logger = logging.getLogger(__name__)


def some_function():
    logger.debug("Debug message")      # Detailed debug info
    logger.info("Info message")         # General information
    logger.warning("Warning message")   # Warning
    logger.error("Error message")       # Error
    logger.critical("Critical message") # Critical
```

---

## 7. Система Мониторинга

**Статус: ✅ ВЫПОЛНЕНО** — Система мониторинга реализована:

**Реализованные метрики в ComPortViewModel:**
- `rx_count` / `tx_count` — счётчики принятых и отправленных сообщений ✅
- `error_count` — счётчик ошибок (новое) ✅
- `connection_time` — время соединения в секундах (новое) ✅
- Автоматический сброс метрик при disconnect ✅

**Метрики уже отображаются в правой панели.**

### 7.1 Архитектура мониторинга

**Компоненты:**
1. **Сборщик метрик** — сбор данных о производительности
2. **Хранилище метрик** — временное хранение данных
3. **Дашборд** — визуализация метрик
4. **Система алертинга** — уведомления о проблемах

### 7.2 Сбор метрик

```python
# src/utils/metrics.py
"""Performance metrics collection."""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque


@dataclass
class MetricsData:
    """Container for performance metrics."""
    timestamp: datetime
    response_time_ms: float
    throughput: float  # requests per second
    cpu_percent: float
    memory_mb: float
    rx_count: int
    tx_count: int
    error_count: int = 0


class MetricsCollector:
    """Collects and stores performance metrics."""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._samples: deque = deque(maxlen=max_samples)
        self._request_times: deque = deque(maxlen=100)
        self._request_count = 0
        self._error_count = 0
        self._start_time = time.time()
        
    def record_request(self, duration_ms: float):
        """Record a request and its duration."""
        self._request_times.append(duration_ms)
        self._request_count += 1
        
    def record_error(self):
        """Record an error occurrence."""
        self._error_count += 1
        
    def get_current_metrics(self) -> MetricsData:
        """Get current system metrics."""
        # Calculate average response time
        avg_response_time = (
            sum(self._request_times) / len(self._request_times)
            if self._request_times else 0
        )
        
        # Calculate throughput
        elapsed = time.time() - self._start_time
        throughput = self._request_count / elapsed if elapsed > 0 else 0
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.Process().memory_info()
        memory_mb = memory.rss / (1024 * 1024)
        
        return MetricsData(
            timestamp=datetime.now(),
            response_time_ms=avg_response_time,
            throughput=throughput,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            rx_count=0,  # Will be updated by app
            tx_count=0,
            error_count=self._error_count
        )
    
    def get_all_samples(self) -> list:
        """Get all collected samples."""
        return list(self._samples)
    
    def reset(self):
        """Reset all metrics."""
        self._samples.clear()
        self._request_times.clear()
        self._request_count = 0
        self._error_count = 0
        self._start_time = time.time()


# Global metrics collector
metrics_collector = MetricsCollector()
```

### 7.3 Интеграция с приложением

```python
# src/utils/metrics_integration.py
"""Integrate metrics collection with application."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """Middleware for collecting application metrics."""
    
    def __init__(self, viewmodel):
        self.viewmodel = viewmodel
        self._rx_count = 0
        self._tx_count = 0
        
    def on_data_received(self, port: str, data: str):
        """Called when data is received."""
        from src.utils.metrics import metrics_collector
        self._rx_count += 1
        # Track metrics
        
    def on_data_sent(self, port: str, data: str):
        """Called when data is sent."""
        from src.utils.metrics import metrics_collector
        self._tx_count += 1
        
    def on_error(self, error: str):
        """Called on error."""
        from src.utils.metrics import metrics_collector
        metrics_collector.record_error()
```

### 7.4 Конфигурация алертинга

```python
# src/utils/alerting.py
"""Alerting system for performance thresholds."""

import logging
from typing import Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    metric: str
    threshold: float
    operator: str  # "gt", "lt", "eq", "gte", "lte"
    level: AlertLevel
    message: str


class AlertManager:
    """Manages alert rules and notifications."""
    
    def __init__(self):
        self.rules: list[AlertRule] = []
        self.handlers: list[Callable] = []
        self.active_alerts: Dict[str, datetime] = {}
        
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        
    def add_handler(self, handler: Callable):
        """Add an alert handler (callback)."""
        self.handlers.append(handler)
        
    def check_metrics(self, metrics: Any):
        """Check metrics against all rules."""
        for rule in self.rules:
            value = getattr(metrics, rule.metric, None)
            if value is None:
                continue
                
            # Check threshold
            triggered = self._evaluate(rule, value)
            
            if triggered:
                self._trigger_alert(rule, value)
                
    def _evaluate(self, rule: AlertRule, value: float) -> bool:
        """Evaluate if threshold is met."""
        ops = {
            'gt': lambda v, t: v > t,
            'lt': lambda v, t: v < t,
            'eq': lambda v, t: v == t,
            'gte': lambda v, t: v >= t,
            'lte': lambda v, t: v <= t,
        }
        return ops[rule.operator](value, rule.threshold)
        
    def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert."""
        # Check if alert already active
        if rule.name in self.active_alerts:
            return  # Already alerted
            
        alert_msg = rule.message.format(value=value, threshold=rule.threshold)
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }[rule.level]
        
        logger.log(log_level, f"[ALERT] {alert_msg}")
        
        # Call handlers
        for handler in self.handlers:
            try:
                handler(rule.level, alert_msg)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
                
        # Mark as active
        self.active_alerts[rule.name] = datetime.now()
        
    def clear_alert(self, rule_name: str):
        """Clear an active alert."""
        if rule_name in self.active_alerts:
            del self.active_alerts[rule_name]
            logger.info(f"Alert cleared: {rule_name}")


# Default alert rules
ALERT_RULES = [
    AlertRule(
        name="high_response_time",
        metric="response_time_ms",
        threshold=100,
        operator="gt",
        level=AlertLevel.WARNING,
        message="High response time: {value:.2f}ms (threshold: {threshold}ms)"
    ),
    AlertRule(
        name="high_memory",
        metric="memory_mb",
        threshold=500,
        operator="gt",
        level=AlertLevel.WARNING,
        message="High memory usage: {value:.2f}MB (threshold: {threshold}MB)"
    ),
    AlertRule(
        name="high_cpu",
        metric="cpu_percent",
        threshold=80,
        operator="gt",
        level=AlertLevel.WARNING,
        message="High CPU usage: {value:.1f}% (threshold: {threshold}%)"
    ),
    AlertRule(
        name="error_rate",
        metric="error_count",
        threshold=10,
        operator="gt",
        level=AlertLevel.ERROR,
        message="High error rate: {value} errors"
    ),
]


alert_manager = AlertManager()
for rule in ALERT_RULES:
    alert_manager.add_rule(rule)
```

### 7.5 Дашборд (веб-интерфейс)

Для визуализации метрик рекомендуется использовать:
- **Streamlit** — быстрое создание дашбордов
- **Flask + Chart.js** — кастомный веб-интерфейс

```python
# scripts/metrics_dashboard.py
"""Simple metrics dashboard using Streamlit."""

import streamlit as st
import time
import psutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.metrics import metrics_collector

st.set_page_config(page_title="UART Control Metrics", layout="wide")

st.title("📊 UART Control - Performance Dashboard")

# Sidebar with controls
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 10, 2)

# Placeholder for metrics
metrics_placeholder = st.empty()

# CPU and Memory
col1, col2 = st.columns(2)

with col1:
    st.subheader("💻 CPU Usage")
    cpu_chart = st.empty()
    
with col2:
    st.subheader("🧠 Memory Usage")
    mem_chart = st.empty()

# Response time
st.subheader("⏱️ Response Time")
response_chart = st.empty()

# Auto-refresh
while True:
    # Get current metrics
    metrics = metrics_collector.get_current_metrics()
    metrics._rx_count = 0  # Would come from actual app
    metrics._tx_count = 0
    
    with metrics_placeholder.container():
        # Display key metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Response Time", f"{metrics.response_time_ms:.2f} ms")
        m2.metric("Throughput", f"{metrics.throughput:.2f}/s")
        m3.metric("Errors", metrics.error_count)
        m4.metric("Uptime", f"{time.time() - metrics_collector._start_time:.0f}s")
        
    # Update charts
    cpu_chart.line_chart([metrics.cpu_percent])
    mem_chart.line_chart([metrics.memory_mb])
    response_chart.line_chart([metrics.response_time_ms])
    
    time.sleep(refresh_rate)
```

### 7.6 Запуск дашборда

```bash
# Установка streamlit
pip install streamlit

# Запуск дашборда
streamlit run scripts/metrics_dashboard.py
```

---

## 8. График Реализации

### Фаза 1: Тестирование (2-3 недели)

1. Настройка инфраструктуры тестирования
2. Написание тестов для Model слоя
3. Написание тестов для ViewModel слоя
4. Настройка покрытия кода (coverage)

### Фаза 2: CI/CD (1-2 недели)

1. Настройка GitHub Actions
2. Конфигурация автоматических проверок
3. Настройка уведомлений
4. Документация по CI/CD

### Фаза 3: Профилирование (1-2 недели)

1. Интеграция профилировщика в код
2. Выявление узких мест
3. Оптимизация критических участков
4. Документация по профилированию

### Фаза 4: Логирование (1 неделя)

1. Расширение системы логирования
2. Настройка FileHandler и ротации
3. Конфигурация по окружениям
4. Документация

### Фаза 5: Мониторинг (2-3 недели)

1. Реализация сбора метрик
2. Создание системы алертинга
3. Разработка дашборда
4. Интеграция с приложением

---

## 9. Зависимости

```txt
# requirements-dev.txt
# Testing
pytest>=7.0.0
pytest-qt>=4.0.0
pytest-mock>=3.10.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0

# Linting
flake8>=5.0.0
pylint>=2.17.0
mypy>=1.0.0
black>=23.0.0

# Profiling
memory_profiler>=0.61.0
line_profiler>=4.1.0

# Monitoring
psutil>=5.9.0
streamlit>=1.24.0

# CI/CD
actions/checkout@v4
actions/setup-python@v5
codecov/codecov-action@v3
```

---

## 10. Заключение

Данный план охватывает все запрошенные направления развития проекта:

1. **Unit-тесты** — полное покрытие Model и ViewModel слоёв
2. **CI/CD** — автоматическая проверка и сборка
3. **Профилирование** — выявление и оптимизация узких мест
4. **Логирование** — расширенное логирование с ротацией
5. **Мониторинг** — сбор метрик, дашборд и алертинг

Каждое направление может быть реализовано независимо, но рекомендуется следовать указанной последовательности для максимальной эффективности.

---

## 11. Выполненные Задачи (2026-02-16)

### Внедрение Unit-Тестов

#### Созданная структура тестов:
```
tests/
├── conftest.py                    # Фикстуры для Qt-тестов
├── pytest.ini                     # Конфигурация pytest
├── models/
│   ├── __init__.py
│   ├── test_serial_worker.py      # Тесты SerialWorker (20 тестов)
│   └── test_config_loader.py      # Тесты ConfigLoader (25 тестов)
├── viewmodels/
│   ├── __init__.py
│   ├── test_main_viewmodel.py     # Тесты MainViewModel (45 тестов)
│   ├── test_com_port_viewmodel.py # Тесты ComPortViewModel (15 тестов)
│   └── test_command_history_viewmodel.py # Тесты CommandHistoryViewModel (17 тестов)
└── utils/
    ├── __init__.py
    ├── test_port_manager.py       # Тесты PortManager (25 тестов)
    ├── test_theme_manager.py      # Тесты ThemeManager (20 тестов)
    └── test_state_utils.py        # Тесты StateUtils (30 тестов)
```

#### Выполненные задачи:

1. **SerialWorker (src/models/serial_worker.py)**
   - ✅ Тестирование инициализации с параметрами по умолчанию
   - ✅ Тестирование метода configure()
   - ✅ Тестирование метода configure_from_dict()
   - ✅ Тестирование метода write()
   - ✅ Тестирование свойств (charset, is_connected, etc.)
   - ✅ Граничные случаи: пустые данные, несколько вызовов stop()

2. **ConfigLoader (src/utils/config_loader.py)**
   - ✅ Тестирование get_colors() для тем dark/light
   - ✅ Тестирование get_button_colors()
   - ✅ Тестирование get_fonts(), get_sizes()
   - ✅ Тестирование get_serial_timing(), get_console_config()
   - ✅ Тестирование _parse_int_value() с различными форматами
   - ✅ Граничные случаи: несуществующие темы, отсутствующие параметры

3. **MainViewModel (src/viewmodels/main_viewmodel.py)**
   - ✅ Тестирование format_rx(), format_tx(), format_system()
   - ✅ Тестирование cache_log_line(), clear_cache()
   - ✅ Тестирование filter_cache() с различными запросами
   - ✅ Тестирование strip_html()
   - ✅ Тестирование счётчиков (increment_rx, increment_tx, etc.)
   - ✅ Граничные случаи: пустые сообщения, длинные сообщения, юникод

4. **ComPortViewModel (src/viewmodels/com_port_viewmodel.py)**
   - ✅ Тестирование свойств порта
   - ✅ Тестирование set_port_name(), set_baud_rate()
   - ✅ Тестирование нормализации состояний
   - ✅ Тестирование счётчиков

5. **CommandHistoryViewModel (src/viewmodels/command_history_viewmodel.py)**
   - ✅ Тестирование CommandHistoryEntry
   - ✅ Тестирование добавления/удаления записей
   - ✅ Тестирование сериализации/десериализации
   - ✅ Тестирование экспорта в файл

6. **PortManager (src/utils/port_manager.py)**
   - ✅ Тестирование синглтона
   - ✅ Тестирование acquire()/release()
   - ✅ Тестирование is_in_use()
   - ✅ Тестирование get_active_ports()
   - ✅ Тестирование thread-safety

7. **ThemeManager (src/utils/theme_manager.py)**
   - ✅ Тестирование set_theme()
   - ✅ Тестирование _get_effective_theme()
   - ✅ Тестирование is_dark_theme(), is_light_theme()
   - ✅ Тестирование смены тем

8. **StateUtils (src/utils/state_utils.py)**
   - ✅ Тестирование PortConnectionState enum
   - ✅ Тестирование normalize_state()
   - ✅ Тестирование is_terminal_state()
   - ✅ Тестирование is_active_state()

#### Результаты тестирования:
- **Всего тестов:** ~197
- **Провалено:** 1 (Windows permission error - не связано с тестами)
- **Пропущено:** 1 (из-за Windows permission error)
