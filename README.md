# Modern UART Control

**Version:** 1.0.0 (tag: v1.0.0)

Современное приложение для управления COM портами с поддержкой одновременной работы с несколькими портами.

## Особенности

- 🎨 **Дизайн Liquid Glass** - Современный интерфейс с эффектом жидкого стекла
- 🌍 **Мультиязычность** - Поддержка Русского и Английского языков
- 🌓 **Темы оформления** - Светлая и темная тема
- 📡 **Управление 3 COM портами** - Одновременная работа с несколькими портами
- 🏗️ **Архитектура MVVM** - Чистая архитектура с разделением моделей, представлений и логики
- ⚡ **Асинхронная обработка** - Неблокирующее взаимодействие с портами

## Структура проекта

```
d:/7_Test_SW/10_Modern-UART_CTRL/
├── src/
│   ├── main.py                 # вход через AppBootstrap
│   ├── bootstrap/              # подготовка QApplication, splash
│   ├── views/
│   │   ├── main_window.py      # адаптивные панели, quick blocks
│   │   ├── console_panel_view.py
│   │   ├── quick_blocks_panel.py
│   │   ├── port_panel_view.py
│   │   └── splash_screen.py
│   ├── viewmodels/
│   │   ├── main_viewmodel.py
│   │   ├── com_port_viewmodel.py
│   │   ├── command_history_viewmodel.py
│   │   └── protocols.py / factory.py
│   ├── utils/
│   │   ├── config_loader.py / config.defaults.ini
│   │   ├── quick_blocks_repository.py + quick_blocks_schema.py
│   │   ├── icon_cache.py / theme_manager.py / translator.py
│   │   └── transmission_settings.py
│   ├── styles/
│   │   ├── app_optimized.qss
│   │   └── constants.py
│   ├── translations/
│   │   ├── en_US.py, ru_RU.py
│   └── smoke_run.py, main.py
├── requirements.txt            # Зависимости проекта
├── tests/                      # Тесты
└── README.md                   # Этот файл
```

## Требования

- Python 3.9+
- PySide6 6.10.2
- pyserial 3.5

## Установка

### 1. Создание виртуального окружения

```bash
python -m venv venv
```

### 2. Активация виртуального окружения

**Windows (PowerShell):**
```powershell
& .\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

## Сборка исполнимых файлов

Перед сборкой убедитесь, что зависимости установлены (`pip install -r requirements.txt`).

### Windows (PowerShell / CMD)

```powershell
python -m pip install --upgrade pyinstaller
packaging\build_windows.bat
```

Скрипт активирует venv, очищает `build/` и `dist/`, убеждается что PyInstaller доступен и вызывает [`packaging/OrbSterm.spec`](packaging/OrbSterm.spec). Готовый билд появится в `dist/OrbSterm`.

### Linux / WSL / macOS

```bash
python -m pip install --upgrade pyinstaller
bash packaging/build_linux.sh
```

Скрипт ожидает активированное `.venv`, запускает PyInstaller с тем же spec-файлом и формирует `dist/OrbSterm`.

## Запуск приложения

Рекомендуемый способ запуска — через обёртки в `scripts/` (поддерживает venv activation):

PowerShell:
```powershell
.
scripts\run.ps1
```

CMD / Batch:
```cmd
scripts\run.bat
```

Прямой запуск (в активированном venv):
```bash
python src/main.py
```

## Запуск тестов

Через `pytest` (рекомендуется):

```bash
python -m pytest -q tests/
```

Альтернатива — старые обёртки в корне:

PowerShell:
```powershell
.\test_final_validation.py
```

## Использование

### Quick Blocks

- Быстрые команды организованы по группам; каждая карточка хранит `command_on/command_off`, целевой порт и хоткей.
- Редактирование/дублирование/удаление происходит прямо в панели, изменения автоматически сохраняются в [`config/quick_blocks.yaml`](config/quick_blocks.yaml).
- Ошибки конфигурации валидируются при загрузке через [`QuickBlocksDocument`](src/utils/quick_blocks_schema.py:44).

### Service Container

- В [`src/utils/service_container.py`](src/utils/service_container.py:9) реализован thread-safe регистратор singleton-ов.
- Локальные помощники (`get_config_loader`, `get_quick_blocks_repository`) объявлены в [`src/utils/__init__.py`](src/utils/__init__.py:9) и используются Views/ViewModels для получения зависимостей без глобальных импортов.

### Основные функции

1. **Управление портами** — выбирайте COM порт, меняйте скорость/чётность, подключайтесь и отключайтесь напрямую из левого столбца. Для каждго порта доступны счётчики RX/TX и ошибки.
2. **Отправка и история** — блок «Передача данных» поддерживает быстрые кнопки (CPU1/CPU2/TLM/1+2), подсветку активности и историю команд с поиском и экспортом.
3. **Консоль RX/TX** — вкладки CPU1/CPU2/TLM + общий журнал; есть поиск с подсветкой, фильтрами, сохранением логов и объединённым видом.
4. **Quick Blocks** — карточки с готовыми командами и хоткеями, сгруппированные по категориям, синхронно обновляются в YAML.
5. **Переключение тем и языка** — пункт меню «Вид» → «Тема/Язык», а также иконка языка в статус-баре.

### Параметры COM порта

- **Скорость передачи** — стандартные значения 9600…115200, дополнительная настройка подключаемых портов автоматически синхронизируется с панелью view.
- **Биты данных** — 5/6/7/8 (см. [`SerialConfig`](src/styles/constants.py:254)).
- **Чётность** — None/Even/Odd/Mark/Space, переключается непосредственно в панели порта.
- **Стоп-биты** — 1/1.5/2.

## Архитектура

Приложение использует паттерн **MVVM** (Model-View-ViewModel):

- **Model** - Содержит логику работы с данными и состоянием приложения
- **View** - Отвечает за представление данных пользователю
- **ViewModel** - Связывает Model и View, содержит логику представления

### Основные компоненты

#### Model Layer
- `serial_worker.SerialWorker` — фоновые потоки для чтения/записи портов.
- `config_loader.ConfigLoader` — централизованный доступ к INI/цветам/размерам.

#### ViewModel Layer
- `MainViewModel` — форматирование RX/TX, кеш логов, фильтрация и счётчики.
- `ComPortViewModel` — управление состоянием порта, очередью отправки, retry.
- `CommandHistoryViewModel` — хранение и фильтрация истории команд.

#### View Layer
- `MainWindow` — связывает панель портов, консоль, quick blocks, статус-бар.
- `ConsolePanelView` — вкладки логов, поиск, подсветка совпадений.
- `QuickBlocksPanel` — карточки команд с группами и контекстными действиями.
- `SplashScreen`/`ToastNotification` — визуальные вспомогательные элементы.

#### Utilities
- `Translator` — локализация с сигналами `language_changed`.
- `ThemeManager` — переключение тем, масштабирование интерфейса.
- `IconCache` — кеширование QIcon в зависимости от темы.

## Переводы

Приложение поддерживает:
- 🇷🇺 Русский (ru_RU)
- 🇬🇧 Английский (en_US)

Переводы хранятся в файлах `/src/translations/` и могут быть легко расширены.

## Темы оформления

### Темная тема
- Основной фон: #1e1e1e
- Вторичный фон: #2d2d2d
- Текст: #ffffff
- Акцент: #007aff

### Светлая тема
- Основной фон: #ffffff
- Вторичный фон: #f5f5f5
- Текст: #000000
- Акцент: #007aff

## Разработка

### Добавление новых переводов

Отредактируйте файлы в `/src/translations/`:

```python
TRANSLATIONS = {
    "key_name": "Translation text",
    # ...
}
```

### Профилирование

Для анализа производительности используйте `scripts/profile_app.py`:

```powershell
.\.venv\Scripts\python scripts/profile_app.py
```

Скрипт запускает приложение под `cProfile` и сохраняет результаты в `logs/profiles/`. Для point-in-time профиля отдельных операций воспользуйтесь [`PerformanceTimer`](src/utils/profiler.py:1) и переменной окружения `APP_PROFILE=true`.

## Лаунчер и доставка

1. Упакуйте ресурсы для кастомного лаунчера:
   ```bash
   python scripts/package_resources.py
   ```
   В каталоге `build/resources/` появятся `resources.zip` и `manifest.json` для проекта [`launcher/`](launcher/README.md).
2. Сборка Windows-билда: `packaging/build_windows.bat` (требует активного `.venv`).
3. Сборка Linux-билда: `bash packaging/build_linux.sh`.

## Лицензия

MIT License

## Автор

Александр Сеченович

## Контакты

- Email: example@example.com
- GitHub: https://github.com/username

## Рождение проекта

Дата создания: 9 февраля 2026
## Сборка собственного загрузчика

1. Сформируйте архив ресурсов:
   ```bash
   python scripts/package_resources.py
   ```
   Архив `build/resources/resources.zip` + `manifest.json` будет использован кастомным загрузчиком.

2. Соберите лаунчер (C++/C# проект в каталоге `launcher/`, TODO).

3. Упакуйте установщик (NSIS/Inno Setup) из содержимого `installer/`.
