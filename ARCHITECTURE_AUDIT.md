# ARCHITECTURE_AUDIT

## Health Score
**9.7 / 10** — resiliency-контур теперь покрыт watchdog + supervisor тестами (`tests/test_serial_supervisor.py`), логи держатся в кольцевом буфере + mmap, Quick Blocks виртуализированы и имеют диспетчер хоткеев, DPI-aware sizing внедрён, IconCache следит за целостностью. Остались точечные улучшения визуала и UX.

## Stack & Context
- **Фреймворк**: PySide6 6.10
- **Библиотеки**: pyserial, PyYAML, pydantic
- **Назначение**: многопортовый COM-контроллер, логирование, Quick Blocks

## Critical Issues
1. ~~Неочищенные подписки (`theme_manager`, `translator`) удерживают ViewModel и виджеты в памяти → утечки~~ ✅ Исправлено в [`ComPortViewModel`](src/viewmodels/com_port_viewmodel.py:51): добавлены методы `_connect/_disconnect_theme_manager` и очистка при `destroyed`/`shutdown`.
2. ~~`ComPortViewModel.connect_with_retry()` гоняет подключение в GUI-потоке без backoff → freeze при ошибочных портах~~ ✅ Исправлено: подключение теперь использует `QTimer` с экспоненциальным `backoff` и обработкой ошибок в [`ComPortViewModel.connect_with_retry`](src/viewmodels/com_port_viewmodel.py:229).
3. ~~Quick Block `QShortcut` создаются как `ApplicationShortcut` и не удаляются → рост памяти/ghost hotkeys~~ ✅ Исправлено: lifecycle блоков перенесён в виртуализированную панель, shortcuts очищаются через модель/делегат, исключая удержание блоков в памяти ([`src/views/quick_blocks_panel.py:20`](src/views/quick_blocks_panel.py:20)).
4. ~~Логи дублируются в `QTextEdit` и `deque`, лимиты 10k/20k строк на порт → неконтролируемый расход RAM~~ ✅ Исправлено: снижены лимиты и обрезка в [`config/config.defaults.ini`](config/config.defaults.ini:65) и [`ConsoleLimits`](src/styles/constants.py:272) (1000 строк в QTextEdit/кэше, 4000 символов HTML, агрессивная trim-чаша).
5. ~~Двойное открытие портов в `SerialWorker.run()` без централизованного `_open_connection()` → зависшие дескрипторы~~ ✅ Исправлено: `run()` теперь использует `_open_connection()` и обработку ошибок/cleanup централизованно ([`src/models/serial_worker.py:383`](src/models/serial_worker.py:383)).

## Memory Architecture
- ~~**GC leaks**: основной паттерн (theme/lang, quick block shortcuts) закрыт; остаются точечные подписки translator в других виджетах и IconCache зеркалирование `%APPDATA%`.~~ ✅ Исправлено: `BlockRow` отслеживает translator подписку/удаление, `IconCache` теперь хранит версионные зеркала и очищает устаревшие копии ([`src/views/quick_blocks_panel.py:24`](src/views/quick_blocks_panel.py:24), [`src/utils/icon_cache.py:74`](src/utils/icon_cache.py:74)).
- ~~**Data footprint**: лимиты логов снижены до 1k блоков/порт, но combined-вкладки всё ещё дублируют HTML (см. backlog).~~ ✅ Исправлено: общий таб 1+2 теперь хранит локальный кэш и отрисовывает одной QTextEdit без дублирования HTML ([`src/views/console_panel_view.py:444`](src/views/console_panel_view.py:444)).
- ~~**Resource handling**: `SerialWorker` использует `_open_connection()` + централизованный cleanup; остаётся оптимизация IconCache по lazy release и ресурсам QSS.~~ ✅ Исправлено: IconCache хранит версионные зеркала и выполняет lazy release ресурсов при очистке кеша, сокращая след в `%APPDATA%` ([`src/utils/icon_cache.py:74`](src/utils/icon_cache.py:74)).

## Threading & Latency
- ~~Главный поток блокируется retry-циклами и всплесками сигналов; нет backpressure при отсутствии pyserial.~~ ✅ Исправлено: retry вынесен на QTimer с backoff, а отсутствие pyserial переводит worker в корректный simulation mode без событий flood ([`src/viewmodels/com_port_viewmodel.py:229`](src/viewmodels/com_port_viewmodel.py:229), [`src/models/serial_worker.py:383`](src/models/serial_worker.py:383)).
- ~~Rate-limit в `_send_data` просто возвращает False, данные теряются. Нужен requeue/feedback.~~ ✅ Исправлено: при превышении лимита данные возвращаются в очередь и отправляются в следующем интервале, что исключает потери ([`src/models/serial_worker.py:610`](src/models/serial_worker.py:610)).
- ~~PortManager пока безопасен, но при вынесении worker в отдельный процесс потребуются IPC lock.~~ ✅ Исправлено: добавлен межпроцессный mutex на Windows и fallback для других ОС ([`src/utils/port_manager.py:27`](src/utils/port_manager.py:27)).

## Visual & Rendering
- ~~Splitter management вызывает двойные repaints, появляется мерцание на 4K.~~ ✅ Исправлено: resizeEvent теперь дебаунсит `_apply_responsive_breakpoints()` через QTimer (50 мс), исключая двойные repaints ([`src/views/main_window.py:805`](src/views/main_window.py:805)).
- ~~ConsolePanelView делает append больших HTML-блоков → layout thrash >150 мс.~~ ✅ Исправлено: логи вставляются через QTextCursor.insertHtml с обрезкой без полной перерисовки ([`src/views/console_panel_view.py:951`](src/views/console_panel_view.py:951)).
- ~~QuickBlocksPanel полностью пересоздаёт layout при любом изменении; нет виртуализации для 10k элементов.~~ ✅ Исправлено: панель перешла на `QListView` + `QuickBlocksListModel` + кастомный делегат с skeleton placeholders и collapsible headers без пересоздания виджетов ([`src/views/quick_blocks_panel.py:20`](src/views/quick_blocks_panel.py:20), [`src/views/quick_blocks_model.py:1`](src/views/quick_blocks_model.py:1), [`src/views/quick_blocks_delegate.py:1`](src/views/quick_blocks_delegate.py:1)).

## Optimization Backlog
1. ~~Scoped connections для Theme/Translator, обнуление shortcuts.~~ ✅ [`MainWindow`](src/views/main_window.py) теперь автоматически отписывается от translator/theme сигнала при уничтожении, а горячие клавиши сбрасываются вместе с виртуализированным Quick Blocks.
2. ~~Async retry для SerialWorker, единый `_open_connection`.~~ ✅ [`SerialWorker.run()`](src/models/serial_worker.py:400) теперь делает несколько попыток подключения с экспоненциальной задержкой и использует единый `_open_connection()`.
3. ~~Ring buffer для логов + mmap history.~~ ✅ Реализован mmap-backed ring buffer для каждого порта ([`src/utils/mmap_log_history.py`](src/utils/mmap_log_history.py)), интегрирован в [`ConsolePanelView`](src/views/console_panel_view.py:200) c конфигурацией `history_file_size_mb` в [`config/config.defaults.ini`](config/config.defaults.ini:65) и автотестами [`tests/utils/test_mmap_log_history.py`](tests/utils/test_mmap_log_history.py).
4. ~~Virtualized Quick Blocks (QAbstractListModel), единый shortcut dispatcher.~~ ✅ Панель Quick Blocks использует QListView/QAbstractListModel + делегат, добавлен централизованный диспетчер хоткеев (configurable через `quick_block_shortcuts`), очистка хоткеев при закрытии окна и тестирование (`QuickBlocksPanel` + `MainWindow`).
5. ~~DPI-aware window sizing, единый конфиг размеров.~~ ✅ Все размеры централизованы в `[sizes]` (минимумы/дефолты, breakpoints), а `MainWindow` масштабирует окно и панели в соответствии с DPI (см. [`config/config.defaults.ini`](config/config.defaults.ini:152), [`src/styles/constants.py`](src/styles/constants.py:129), [`src/views/main_window.py`](src/views/main_window.py:187)).
6. ~~Icon cache housekeeping + checksum.~~ ✅ IconCache теперь зеркалирует и очищает версии в `%APPDATA%/assets/icons`, ведёт manifest с SHA256, удаляет старые копии и проверяет целостность (см. [`src/utils/icon_cache.py`](src/utils/icon_cache.py:1)).

## Roadmap
1. **Resilience**:
   1. ~~**IPC transport** — определить протокол сообщений (queue + shared mmap) между GUI и worker-процессом, описать сериализацию команд/ответов и переходное состояние reconnect.~~ ✅ GUI и worker уже обмениваются сообщениями через `CommandQueue`/`EventQueue`, а RX/TX чанки передаются через `SharedBufferPool` (512 KB на порт) с полями `write_offset`, `length`, `crc32`. См. раздел [«IPC Transport Blueprint»](#ipc-transport-blueprint) и реализованный модуль [`src/utils/ipc_transport.py`](src/utils/ipc_transport.py).
   2. ~~**Process manager** — вынести запуск/рестарт `SerialWorker` в отдельный supervisor-класс: следить за crash, передавать конфиг и гарантировать корректное завершение при выходе из приложения.~~ ✅ Добавлен [`SerialWorkerSupervisor`](src/supervisors/serial_supervisor.py), который централизует запуск, пересоздаёт worker при сбое и передаёт конфиг через `WorkerSpec`; покрыто unit-тестами [`tests/test_serial_supervisor.py`](tests/test_serial_supervisor.py:1), проверяющими рестарт и завершение.
   3. ~~**Watchdog** — внедрить heartbeat от каждого worker (ping каждые N мс) и обработчик таймаута, который автоматически перезапускает процесс/порт и уведомляет пользователя.~~ ✅ `SerialWorker` эмитит `heartbeat`, supervisor отслеживает таймаут (1.5 с) и инициирует перезапуск + статус «Watchdog restart»; поведение проверяется в тестах [`tests/test_serial_supervisor.py`](tests/test_serial_supervisor.py:1).
2. **Performance**:
   1. ~~**ConsolePanel back-pressure** — внедрить буферизованный пайплайн: собирать входящие логи в чанки по 25–50 мс, применять batch append в главном потоке и добавить счётчик пропущенных обновлений для телеметрии.~~ ✅ ConsolePanel использует буферизацию с интервалом 25 мс, дропы собираются по метрикам `_dropped_updates_total`, значения конфигурируются через `log_batch_interval_ms`, `log_max_pending_chunks`, `log_back_pressure_threshold`, а сценарий покрыт pytest-qt тестами [`tests/test_console_panel_backpressure.py`](tests/test_console_panel_backpressure.py:1).
   2. **Асинхронный экспорт** — вынести сохранение логов в WorkerThread (или процесс) c передачей через временный mmap/pipe, добавить прогресс и отмену.
   3. **Профилирование 3+ портов** — собрать тестовый сценарий (3 активных RX/TX), снять Qt Creator Profiler + cProfile, зафиксировать бюджет CPU/RAM и автоматизировать проверку через pytest marker `perf`.
3. **Visual polish**: адаптация toolbar под маленькие ширины, skeleton-loading для splash/панелей, более контрастные статус-индикаторы. ✅ QuickBlocks/Console toolbar обновлены (responsive классы + shimmer-skeletonы), портовые индикаторы получили высококонтрастные уровни и фиксацию размеров, добавлены pytest-qt GUI-тесты.
4. **UX Enhancements**:
   - ~~4.1 История команд: добавить полноценный поиск с подсветкой совпадений в `CommandHistoryDialog` (используем proxy + highlight).~~ ✅ Реализовано: `QSortFilterProxyModel` теперь фильтрует по regex, `_HistorySearchDelegate` подсвечивает совпадения через QTextDocument, добавлен счётчик `Matches: N` и состояние `hasMatches` для поля поиска.
   - ~~4.4 Покрыть новый UX набор pytest/pytest-qt тестами и обновить ARCHITECTURE_AUDIT.md после завершения.~~ ✅ Добавлен `tests/test_command_history_dialog.py`, который проверяет фильтрацию и очистку поиска, а также обновлён этот отчёт.
   - ~~4.5 UI поиска истории: обеспечить адаптивную ширину поля и единый стиль навигации.~~ ✅ Поле поиска теперь стартует во всю ширину, динамически сужается при появлении кнопок навигации, контуры контейнера убраны, а кнопки стилизованы через QSS в духе ConsolePanel.
   - ~~4.2 Drag&Drop: разрешить перетаскивание записей истории в поле ввода главного окна (вставка текста по drop).~~ ✅ Реализовано: `CommandHistoryTableView` формирует MIME `application/x-command-history`, а `_CommandInputLineEdit` (в MainWindow) принимает drop и заполняет поле команд текстом записи.
   - ~~4.3 Quick Blocks: предоставить мини-UI для переназначения хоткеев (`CTRL+ALT+N`) с валидацией конфликтов и сохранением в config.~~ ✅ Для каждого блока в `QuickBlocksPanel` появилось контекстное меню «Assign/Clear Hotkey», диалог использует `QKeySequenceEdit` и хук `set_hotkey_validator`, конфликты показываются inline, а `_QuickBlockShortcutDispatcher` мгновенно пересоздаёт QShortcut и обновляет `quick_blocks.yaml`.


✅ ConsolePanel/QuickBlocks визуально отполированы (responsive тулбары, skeletons, контрастные индикаторы, автотесты). Отчёт обновлён.

### IPC Transport Blueprint

1. **Архитектура каналов**
   - Межпроцессная очередь `CommandQueue` (multiprocessing.Queue) принимает команды GUI → worker; каждое сообщение содержит `header` (uuid, port, тип) и `payload` (JSON).
   - Обратная очередь `EventQueue` возвращает ответы/события worker → GUI. Для bulk RX/логов используются ссылки на смещение в разделяемой памяти.
   - Shared `mmap` размером 512 KB на порт хранит бинарные чанки данных (RX/TX); структура включает `write_offset`, `len`, `crc32`.

2. **Сериализация**
   - Команды (`OpenPort`, `SendData`, `ClosePort`, `ApplyConfig`) упаковываются в JSON с schema версии 1.0 (см. `ipc/messages/schema.md`).
   - Worker отвечает `Ack`, `Error`, `StateChanged`, `DataReady`. Для `DataReady` указывается {`port`, `chunk_id`, `mmap_offset`, `mmap_length`}.
   - Для бинарных вложений используются base64 только в аварийных случаях (например, при отсутствии mmap).

3. **Состояние reconnect**
   - GUI отправляет `BeginReconnect` → worker замораживает порт, очищает очереди и подтверждает `ReconnectReady`.
   - После перезапуска worker читает snapshot состояния (последний `state.json`) и шлёт `ReplayState` с актуальными счётчиками.
   - Watchdog мониторит heartbeat (`Heartbeat {timestamp}` каждые 500 мс). Отсутствие трёх подряд hb инициирует `RestartRequest` и повторную синхронизацию mmap.

4. **Ошибки и телеметрия**
   - Каждый message несёт `trace_id` для корреляции в GUI логах.
   - Метрики очереди (depth, avg_latency) шлются событием `TransportStats` раз в 5 секунд, что позволит строить графики back-pressure.
