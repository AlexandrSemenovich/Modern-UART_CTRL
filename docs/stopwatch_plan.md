# План внедрения секундомера

## 1. Контекст и цели

- UI построен вокруг трёх панелей (лево/центр/право) с горизонтальным сплиттером [`python.MainWindow._setup_ui()`](src/views/main_window.py:371).
- Имеется статус-бар, поддержка тем (ThemeManager), переводы, QSS в [`src/styles/app_optimized.qss`](src/styles/app_optimized.qss).
- Требуется секундомер с форматом `dd hh:mm:ss.mmm`, ручным и будущим авто-стартом/сбросом, со стилями приложения. Нужна возможность открыть отдельное окно-виджет и последующие тесты.

## 2. Предлагаемая архитектура секундомера

1. **Сервис уровня utils**
   - Создать `src/utils/stopwatch.py` с классами `StopwatchState` (dataclass) и `StopwatchService` (таймер на `QtCore.QTimer`).
   - Экспортировать API через `service_container`, чтобы ViewModel могла получать singleton.

2. **ViewModel слой**
   - Добавить `StopwatchViewModel` в `src/viewmodels/stopwatch_viewmodel.py`.
   - Внедрить через [`python.ViewModelFactory`](src/viewmodels/factory.py:17) (метод `create_stopwatch_viewmodel`).
   - Сигналы: `time_changed(str)`, `state_changed(StopwatchState)`, методы `start_manual()`, `stop_manual()`, `reset_manual()`, `arm_auto(mode)`.

3. **View слой**
   - Основной виджет: `src/views/widgets/stopwatch_widget.py` (подкласс `QtWidgets.QFrame`).
   - Встраивание в правую панель `MainWindow` рядом с блоком счётчиков ([`python.MainWindow._create_right_panel()`](src/views/main_window.py:663)) как новый `QGroupBox` «Секундомер» сразу под `Counters`.
   - Виджет должен использовать общие константы (`Fonts`, `Sizes`, `theme_manager`).
   - Кнопки (Старт/Стоп/Сброс) оформлять через `_register_button` [`python.MainWindow._register_button()`](src/views/main_window.py:1520) при инициализации, либо через класс стилей `class="primary/secondary/ghost"`.

4. **Окно-виджет**
   - Создать `StopwatchWindow` (`QDialog` либо `QWidget` с `Qt.Tool`) в `src/views/stopwatch_window.py`.
   - Кнопка/действие в меню View (`menubar`) и пункт контекстного меню статус-бара для открытия окна. Действие добавляется в [`python.MainWindow._setup_menu()`](src/views/main_window.py:932).
   - Окно пересоздаёт тот же `StopwatchWidget`, синхронизируя состояние через общую ViewModel (инъекция в конструктор, sharable сигналы).

## 3. Интеграция в существующее UI

1. **Правый скролл-панель**
   - После создания `counters_grp` вставить новый `stopwatch_grp` (GroupBox). Убедиться, что `QScrollArea` растягивается и не ломает макет. Новая секция должна иметь фиксированную минимальную высоту, чтобы не «прыгать» при расширении.
   - В адаптивной логике `_apply_responsive_breakpoints()` ничего менять не нужно: ширина панели фиксирована константами [`python.Sizes.RIGHT_PANEL_MIN_WIDTH`](src/styles/constants.py:1) (прочитать фактические значения для согласования).

2. **Статус-бар**
   - Добавить компактный индикатор (например, `QLabel` с текущим временем) в `statusBar.addPermanentWidget`, синхронно обновляемый ViewModel. Это позволит видеть время даже при скрытом правом блоке.

3. **Горячие клавиши**
   - В `_setup_shortcuts()` добавить `Ctrl+Shift+S` (старт/стоп) и `Ctrl+Shift+R` (reset).

4. **Переводы**
   - Добавить ключи в `src/translations/strings.py` + `en_US.py` и `ru_RU.py` («Stopwatch», «Start», «Stop», «Reset», «Open as widget» и пр.).

## 4. API и состояние

| Событие/метод              | Назначение |
|---------------------------|------------|
| `StopwatchService.start()`| Запуск таймера, фиксирует `start_timestamp`.
| `StopwatchService.reset()`| Сброс счётчика, эмит `elapsed=0`.
| `StopwatchService.set_auto_mode(mode)` | Подготовка будущей автоматизации (hook на внешние сигналы `ComPortViewModel`).
| `StopwatchViewModel.toggle_manual()` | Переключение старт/стоп.
| `StopwatchWidget` slots `update_display(str)` | Обновляет текст в `QLabel`.

Формат `dd hh:mm:ss.mmm` выполняется в сервисе: вычисление `timedelta`, затем форматирование с ведущими нулями и миллисекундами (`f"{days:02d} {hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"`).

## 5. Окно-виджет

1. `StopwatchWindow` хранит ссылку на `StopwatchViewModel`, подписывается на сигналы, передаёт действия кнопок.
2. Режим «tool window»: `self.setWindowFlag(Qt.Tool)` + `self.setAttribute(Qt.WA_DeleteOnClose, False)` чтобы переиспользовать окно.
3. Поддержка тем/локализаций: подключиться к `theme_manager.theme_changed` и `translator.language_changed` аналогично `MainWindow`.

## 6. Тестирование *(выполнено)*

1. **Юнит-тесты utils** — [`tests/utils/test_stopwatch_service.py`](tests/utils/test_stopwatch_service.py:1) переписан без `QSignalSpy`, проверяет формат времени, старт/стоп/сброс и гарантирует эмиссию `StopwatchState`.
2. **ViewModel** — [`tests/viewmodels/test_stopwatch_viewmodel.py`](tests/viewmodels/test_stopwatch_viewmodel.py:1) подтверждает сигналы `time_changed` и команды `start/stop/reset`.
3. **Интеграция View** — [`tests/test_stopwatch_widget.py`](tests/test_stopwatch_widget.py:1) проверяет построение UI и наличие основных виджетов.
4. **Структура** — [`tests/test_structure.py`](tests/test_structure.py:36) содержит проверки существования модулей секундомера.
5. **Следующие улучшения** — добавить smoke-тест `scripts/smoke_run.py` и визуальные snapshot-тесты для поддержания регрессий при будущей автоматизации.

## 7. Пошаговый план реализации

1. **Подготовка файлов** *(выполнено)*
   - ✅ Создать `src/utils/stopwatch.py` и экспортировать сервис.
   - ✅ Обновить `src/utils/__init__.py` и `service_container`.
2. **ViewModel** *(выполнено)*
   - ✅ Добавить `stopwatch_viewmodel.py`, зарегистрировать в `ViewModelFactory`.
3. **Виджет и окно** *(выполнено)*
   - ✅ Создать `StopwatchWidget` и `StopwatchWindow`.
   - ✅ Добавить секцию в правый блок и статус-бар.
4. **Меню и действия** *(выполнено)*
   - ✅ Добавить действие «Открыть секундомер» в меню View + QShortcut + Tray (по необходимости).
5. **Переводы и стили** *(выполнено)*
   - ✅ Добавить строки в `translations`, классы стилей в QSS (например, `.stopwatch-display`).
6. **Тесты**  *(выполнено)*
   - ✅ Реализовать тесты согласно разделу 6 (см. выше).
   - ✅ Добавить smoke-тест запуска приложения с секундомером (`scripts/smoke_run.py`) для проверки UI при разных темах.
7. **Документация** *(в работе)*
   - Обновить [`docs/architecture.md`](docs/architecture.md) коротким описанием секундомера и его связей.
   - Добавить раздел в [`README.md`](README.md) о горячих клавишах секундомера и отдельном окне (для QA).

## 8. Будущая автоматизация

- Запланировать хук на события `ComPortViewModel` (например, авто-старт при установлении соединения, авто-сброс при дисконнекте). ViewModel должен уметь подписываться на сигналы портов, но в первой итерации оставить заглушки `set_auto_mode`.

## 9. Риски и меры

- **Риск ломать вёрстку правой панели:** использовать `QVBoxLayout` и `addStretch()` после новых групп, контролировать `setSizePolicy` для `StopwatchWidget`.
- **Дублирование состояния между окном и панелью:** единый ViewModel + сигналы Qt решают проблему.
- **Производительность:** QTimer на 10–20 мс шаг даёт плавные миллисекунды; можно ограничить обновление label до 50 мс, чтобы не нагружать UI.

