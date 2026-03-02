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

## 5. Конфигурация и данные

- YAML [`config/quick_blocks.yaml`](config/quick_blocks.yaml) хранит пресеты, но отсутствует схема валидации. Добавьте `pydantic`/`jsonschema` в загрузчик (`config_loader`) и флаг «configuration_version» для миграций.
- Файл [`config/config.ini`](config/config.ini) используется одновременно приложением и тестами. Для reproducible builds держите `config.defaults.ini` и перегружайте пользовательские настройки из `%APPDATA%`.
- `assets/icons` разделены по `dark`/`light`, но [`theme_manager`](src/utils/theme_manager.py:?) не кеширует QIcon. Продолжайте расширять [`IconCache`](src/utils/icon_cache.py:?) и подменяйте ресурсы в зависимости от темы для снижения времени отклика.

## 6. Тестирование и качество

- Тесты расположены в [`tests/`](tests/test_main_viewmodel.py:1 и др.), но нет покрытия View слоя/интеграции. Добавьте `pytest-qt` для smoke-тестов окон и baseline скриншотов.
- Нет CI-конфигурации. Создайте GitHub Actions (lint + pytest + packaging smoke) с матрицей Windows/Linux.
- В [`requirements.txt`](requirements.txt:1) указана фиктивная зависимость `pkg-resources==0.0.0`, которая конфликтует с `pip`. Удалите её или используйте `pip freeze` без этого пакета.

## 7. Сборка и доставляемость

- Скрипт [`packaging/build_windows.bat`](packaging/build_windows.bat:1) активирует venv и запускает PyInstaller, но не очищает `dist/` и `build/`. Добавьте `rmdir /s /q build dist` перед сборкой и параметр `--clean`.
- Нет описания пользовательского лаунчера в `README`. Стоит расширить раздел «Сборка собственного загрузчика» ссылкой на `launcher/README.md` и статусом TODO.

## 8. Документация

- Файл [`README.md`](README.md:1) содержит устаревшее описание структуры (`app.qss`/`glass_styles.py` отсутствуют). Обновите дерево и добавьте разделы «Quick Blocks», «Service Container» и «Профилирование».
- Добавьте `docs/architecture.md` с диаграммой потоков данных между `MainWindow`, ViewModels и `serial_worker`.

---

**Следующие шаги:**
1. Привязать CI и автотесты.
2. Ввести адаптивную компоновку для центрального тулбара и боковых панелей.
3. Централизовать конфигурацию/палитру для QSS и ViewModel.
