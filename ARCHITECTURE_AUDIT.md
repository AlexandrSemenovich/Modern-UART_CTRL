# ARCHITECTURE_AUDIT

## Health Score
**8 / 10** — ключевые критические дефекты устранены, система стабильна при типовой нагрузке, остаются точечные риски (IconCache, UI overdraw) и пространство для оптимизации.

## Stack & Context
- **Фреймворк**: PySide6 6.10
- **Библиотеки**: pyserial, PyYAML, pydantic
- **Назначение**: многопортовый COM-контроллер, логирование, Quick Blocks

## Critical Issues
1. ~~Неочищенные подписки (`theme_manager`, `translator`) удерживают ViewModel и виджеты в памяти → утечки~~ ✅ Исправлено в [`ComPortViewModel`](src/viewmodels/com_port_viewmodel.py:51): добавлены методы `_connect/_disconnect_theme_manager` и очистка при `destroyed`/`shutdown`.
2. ~~`ComPortViewModel.connect_with_retry()` гоняет подключение в GUI-потоке без backoff → freeze при ошибочных портах~~ ✅ Исправлено: подключение теперь использует `QTimer` с экспоненциальным `backoff` и обработкой ошибок в [`ComPortViewModel.connect_with_retry`](src/viewmodels/com_port_viewmodel.py:229).
3. ~~Quick Block `QShortcut` создаются как `ApplicationShortcut` и не удаляются → рост памяти/ghost hotkeys~~ ✅ Исправлено: `BlockRow` теперь переиспользует `WidgetWithChildrenShortcut`, очищает `QShortcut` при dispose, а `GroupCard` освобождает их при смене блоков ([`src/views/quick_blocks_panel.py:139`](src/views/quick_blocks_panel.py:139)).
4. ~~Логи дублируются в `QTextEdit` и `deque`, лимиты 10k/20k строк на порт → неконтролируемый расход RAM~~ ✅ Исправлено: снижены лимиты и обрезка в [`config/config.defaults.ini`](config/config.defaults.ini:65) и [`ConsoleLimits`](src/styles/constants.py:272) (1000 строк в QTextEdit/кэше, 4000 символов HTML, агрессивная trim-чаша).
5. ~~Двойное открытие портов в `SerialWorker.run()` без централизованного `_open_connection()` → зависшие дескрипторы~~ ✅ Исправлено: `run()` теперь использует `_open_connection()` и обработку ошибок/cleanup централизованно ([`src/models/serial_worker.py:383`](src/models/serial_worker.py:383)).

## Memory Architecture
- **GC leaks**: основной паттерн (theme/lang, quick block shortcuts) закрыт; остаются точечные подписки translator в других виджетах и IconCache зеркалирование `%APPDATA%`.
- **Data footprint**: лимиты логов снижены до 1k блоков/порт, но combined-вкладки всё ещё дублируют HTML (см. backlog).
- **Resource handling**: `SerialWorker` использует `_open_connection()` + централизованный cleanup; ещё требуется зачистка зеркал IconCache и release графических ресурсов при смене темы.

## Threading & Latency
- Главный поток блокируется retry-циклами и всплесками сигналов; нет backpressure при отсутствии pyserial.
- Rate-limit в `_send_data` просто возвращает False, данные теряются. Нужен requeue/feedback.
- PortManager пока безопасен, но при вынесении worker в отдельный процесс потребуются IPC lock.

## Visual & Rendering
- Splitter management вызывает двойные repaints, появляется мерцание на 4K.
- ConsolePanelView делает append больших HTML-блоков → layout thrash >150 мс.
- QuickBlocksPanel полностью пересоздаёт layout при любом изменении; нет виртуализации для 10k элементов.

## Optimization Backlog
1. Scoped connections для Theme/Translator, обнуление shortcuts.
2. Async retry для SerialWorker, единый `_open_connection`.
3. Ring buffer для логов + mmap history.
4. Virtualized Quick Blocks (QAbstractListModel), единый shortcut dispatcher.
5. DPI-aware window sizing, единый конфиг размеров.
6. Icon cache housekeeping + checksum.

## Roadmap
1. **Stabilization**: lifecycle cleanup, splash guards, config DPI.
2. **Resilience**: Serial retry scheduler, log retention, graceful pyserial absence.
3. **Performance**: console batch insert, ring buffer, splitter policies.
4. **Visual polish**: Quick Blocks virtualization, toolbar адаптация, skeleton loading.

