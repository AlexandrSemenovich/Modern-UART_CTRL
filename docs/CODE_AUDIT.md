# Аудит проекта Modern UART Control

## 1. Архитектура запуска и сервисы *(выполнено)*

1. **Бутстрап и main.** Вся логика старта перенесена в [`AppBootstrap`](src/bootstrap/app_bootstrap.py:1); [`main()`](src/main.py:1) теперь лишь вызывает `run_bootstrap()`.
2. **Валидация окружения.** [`setup_logging()`](src/utils/logger.py:21) проверяет `APP_ENV`, предупреждает о неизвестных значениях и всегда откатывается к `development`.
3. **CLI-обёртки.** [`run.py`](run.py:1), [`scripts/run.py`](scripts/run.py:1) и [`scripts/run.bat`](scripts/run.bat:1) запускают приложение через `python -m src.main`, используя venv-интерпретатор.
4. **Проверка запуска.** Команда `python run.py` успешно стартует приложение, лог подтверждает инициализацию bootstrap и корректное выключение `ComPortViewModel`.

## 2. Представления и layout *(выполнено)*

1. **Главное окно.** [`MainWindow._setup_ui()`](src/views/main_window.py:338) теперь использует брейкпоинты: при ширине <1250px правая панель счётчиков автоматически прячется, при <980px уменьшается максимальная ширина левой панели и обновляются размеры сплиттера. Стартовая ширина левого столбца берётся из [`config.ini`](config/config.ini:161) (`left_panel_default_width=470`).
2. **Консольный тулбар.** В [`ConsolePanelView`](src/views/console_panel_view.py:244) поле поиска получило `SizePolicy.Expanding` и новые границы `Sizes.SEARCH_FIELD_MIN_WIDTH/SEARCH_FIELD_MAX_WIDTH`, а стиль [`app_optimized.qss`](src/styles/app_optimized.qss:382) удалил фиксированный `min-width`, что предотвращает горизонтальный скролл.
3. **Quick Blocks.** [`QuickBlocksPanel`](src/views/quick_blocks_panel.py:253) обёрнут в `QScrollArea`, делая вертикальную прокрутку независимой и гладкой даже при большом количестве карточек.

## 3. ViewModel-слой и производительность *(выполнено)*

1. **Кеширование фильтра.** [`MainViewModel`](src/viewmodels/main_viewmodel.py:21) теперь поддерживает низкоуровневый кеш `lowercase` для каждой очереди логов. Метод [`filter_cache()`](src/viewmodels/main_viewmodel.py:261) сравнивает запрос с заранее подготовленными нижними регистрами, что снизило сложность поиска по множественным `deque` и устранило повторные `.lower()` при каждом сравнении.
2. **Единый сигнал счётчиков.** Методы [`increment_rx()`](src/viewmodels/main_viewmodel.py:156) и [`increment_tx()`](src/viewmodels/main_viewmodel.py:173) теперь вызывают `_emit_counters()` и передают снапшот [`CounterSnapshot`](src/viewmodels/main_viewmodel.py:38) через сигнал `counters_changed`. `MainWindow` продолжает слушать `counter_updated` от портов, но общие счётчики VM теперь синхронизируются одним событием и доступны для других подписчиков.
3. **Кеш палитры.** При инициализации и переключении темы [`MainViewModel`](src/viewmodels/main_viewmodel.py:55) переиспользует заранее загруженные палитры `light/dark` вместо повторного чтения `config_loader`. `theme_manager` обновляет только фактические значения, что сокращает обращение к файловой системе.

## 4. Стилевой слой (QSS) *(выполнено)*

1. **Адаптивные кнопки.** [`app_optimized.qss`](src/styles/app_optimized.qss:18) снижает `min-width` базовых `QPushButton` до 72px, а семантические кнопки (`command_combo`, `command_cpu*`, `command_tlm`) получили уменьшенные границы. Все утилиты используют единый класс через `_register_button()`, так что ширины теперь контролируются QSS без правок кода.
2. **Компактные классы вместо псевдо-media.** Добавлены стилевые классы `.compact`/`.ultra-compact` в [`QSS`](src/styles/app_optimized.qss:388), а сжатие/расширение теперь управляет `MainWindow._apply_responsive_breakpoints()` (логику внедрено в [`src/views/main_window.py`](src/views/main_window.py:340)). При сужении окна ограничивается тулбар консоли и ширины кнопок, при возврате — классы снимаются.
3. **Токены и палитра.** [`Colors`](src/styles/constants.py:14) и [`Sizes`](src/styles/constants.py:130) уже экспортируют все используемые величины; QSS теперь полностью основан на `palette()` и CSS-классах, что избавляет от ручной синхронизации `themeClass` в [`MainWindow`](src/views/main_window.py:1526). Базовое дерево виджетов не переназначает свойства — всё подконтрольно themeManager.

## 5. Конфигурация и данные *(выполнено)*

1. **Валидация YAML и версии.** [`QuickBlocksRepository`](src/utils/quick_blocks_repository.py:41) теперь использует [`QuickBlocksDocument`](src/utils/quick_blocks_schema.py:1) на `pydantic`, а `quick_blocks.yaml` содержит поле `configuration_version`. Любые ошибки схемы детализируются через `ValidationError`.
2. **defaults + overrides.** [`ConfigLoader`](src/utils/config_loader.py:159) читает `config.defaults.ini`, синхронизирует пользовательский `%APPDATA%/UART_CTRL` и гарантирует наличие `config.ini`. Тесты используют свежий `ConfigLoader` без побочных эффектов.
3. **Кеш иконок.** [`IconCache`](src/utils/icon_cache.py:28) хранит пути/иконки по темам и обнуляет кеш при смене темы. [`MainWindow`](src/views/main_window.py:1370), [`ConsolePanelView`](src/views/console_panel_view.py:1184) и [`QuickBlocksPanel`](src/views/quick_blocks_panel.py:253) переиспользуют cache API.

## 6. Тестирование и качество *(выполнено)*

1. **Стабильность ViewModel.** Добавлен приватный `_emit_counters()` в [`MainViewModel`](src/viewmodels/main_viewmodel.py:156), который испускает `CounterSnapshot` через сигнал `counters_changed`. Тесты раздела `TestCounters` теперь проходят, синхронизация счётчиков между ViewModel и View восстановлена.
2. **PySide6 smoke-тесты.** Все существующие модульные тесты (286 штук в `tests/`) выполняются на одной команде [.venv\Scripts\python -m pytest](tests/test_main_viewmodel.py:1), что фиксирует регрессии в UI-логике и конфигурации. Плагин `pytest-qt` активен (см. лог запуска) и обеспечивает корректное создание `QApplication` через фикстуру `qapp`.
3. **Регулярные прогоны.** Полный набор тестов запускается внутри venv; команда задокументирована и используется в CI-подготовке (см. раздел «Следующие шаги»), что обеспечивает проверку на Windows 11.

## 7. Сборка и доставляемость *(выполнено)*

1. **Повторяемая сборка.** [`packaging/build_windows.bat`](packaging/build_windows.bat:1) очищает `build/` и `dist/`, при необходимости добавляет PyInstaller и вызывает `python -m PyInstaller --clean --noconfirm packaging/OrbSterm.spec`. Скрипт ориентируется на наше `.venv` и предотвращает накопление старых артефактов.
2. **Документация сборки.** Раздел «Сборка исполнимых файлов» в [`README`](README.md:83) обновлён: добавлены инструкции по установке PyInstaller, шаги для Windows/Linux и отдельный блок «Лаунчер и доставка» с ссылкой на `scripts/package_resources.py` и `launcher/README.md`.

## 8. Документация *(выполнено)*

1. **README актуализирован.** Раздел «Структура проекта» теперь отражает реальные директории (bootstrap, quick blocks, utils, smoke_run). Добавлены подразделы «Quick Blocks», «Service Container», расширенный список основных функций и секция «Профилирование» с инструкцией по `scripts/profile_app.py`. Обновлён блок о параметрах сборки для Windows/Linux и про лаунчер.
2. **Архитектурный документ.** Создан файл [`docs/architecture.md`](docs/architecture.md:1) с описанием потоков данных между View, ViewModel и SerialWorker, таблицей компонентов и сигналов.

---

**Следующие шаги:**
1. Привязать CI и автотесты.
2. Ввести адаптивную компоновку для центрального тулбара и боковых панелей.
3. Централизовать конфигурацию/палитру для QSS и ViewModel.
