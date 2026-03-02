# Архитектура Modern UART Control

Документ описывает поток данных между View (PySide6), ViewModel слоем и низкоуровневыми модулями.

```
┌──────────┐    пользовательские действия     ┌────────────┐
│  Views   │ ── сигнал/слот (Qt, PySide6) ──> │ ViewModels │
│ (Qt UI)  │ <─ обновления моделей ───────────│ (QObject)  │
└──────────┘                                   └────────────┘
       │                                            │
       │ логирование / счётчики, cache              │ обращения
       ▼                                            ▼
┌────────────────────┐     YAML/INI/ресурсы    ┌───────────────────────┐
│ QuickBlocksRepository │ <─> config_loader ─> │  utils (icon_cache,    │
│ CommandHistory etc.  │                      │  translator, theme)    │
└────────────────────┘                      └───────────────────────┘
       │                                            │
       │ обновления состояния портов                │ темы/локализация
       ▼                                            ▼
┌────────────────────┐                      ┌───────────────────────┐
│ ComPortViewModel   │ ── сигналы ────────> │ ConsolePanelView      │
│ SerialWorker (QThread)│                   │ QuickBlocksPanel      │
└────────────────────┘                      └───────────────────────┘
```

## Главные компоненты

| Слой     | Файл/класс                                  | Роль |
|----------|---------------------------------------------|------|
| View     | [`MainWindow`](../src/views/main_window.py) | Управляет панелями портов/консоли, подписывается на `ViewModelFactory`. |
| View     | [`ConsolePanelView`](../src/views/console_panel_view.py) | Отображает RX/TX логи, поиск, подсветку. |
| ViewModel| [`MainViewModel`](../src/viewmodels/main_viewmodel.py) | Форматирует сообщения, ведёт счётчики и кеш логов, испускает `counters_changed`. |
| ViewModel| [`ComPortViewModel`](../src/viewmodels/com_port_viewmodel.py) | Управляет состоянием конкретного порта, очередью отправки, сигналами для UI. |
| Model    | [`SerialWorker`](../src/models/serial_worker.py) | QThread для отправки/приёма данных, сообщает ViewModel о событиях. |
| Utils    | [`ConfigLoader`](../src/utils/config_loader.py) | Грузит defaults, цвета, размеры, настройки сериализации. |
| Utils    | [`QuickBlocksRepository`](../src/utils/quick_blocks_repository.py) + [`QuickBlocksDocument`](../src/utils/quick_blocks_schema.py) | YAML-хранилище быстрых команд с валидацией Pydantic. |
| Utils    | [`IconCache`](../src/utils/icon_cache.py) | Кеширует QIcon по активной теме, рассылает обновления. |
| Utils    | [`ThemeManager`](../src/utils/theme_manager.py) | Применяет QSS, масштабирует UI, сигнализирует о смене темы. |

## Потоки данных

1. Пользователь нажимает кнопку `Отправить` в [`MainWindow`](../src/views/main_window.py). View вызывает `_send_command()`, которая делегирует в нужный [`ComPortViewModel`](../src/viewmodels/com_port_viewmodel.py).
2. `ComPortViewModel` передаёт данные в [`SerialWorker`](../src/models/serial_worker.py). Успешная отправка испускает сигнал `send_completed`, ошибки — `error_occurred`.
3. При приёме данных `SerialWorker` сигналит `data_received`, ViewModel форматирует текст через [`MainViewModel.format_rx`](../src/viewmodels/main_viewmodel.py#L114) и передаёт в [`ConsolePanelView`](../src/views/console_panel_view.py) для отображения и кеширования.
4. Изменения темы/языка инициируют события `theme_manager.theme_changed` и `translator.language_changed`, на которые подписаны `IconCache`, `ConsolePanelView`, `QuickBlocksPanel` и другие View-классы.
5. Quick Blocks редактируются во View (`QuickBlocksPanel`), затем вызывают методы [`QuickBlocksRepository`](../src/utils/quick_blocks_repository.py) для записи YAML; при перечитывании используется схема [`QuickBlocksDocument`](../src/utils/quick_blocks_schema.py) для валидации.

## Сигналы и события

- `ComPortViewModel.state_changed` → `PortPanelView` переключает кнопку Connect.
- `ComPortViewModel.counter_updated` → `MainWindow` обновляет счётчики RX/TX.
- `MainViewModel.counters_changed` → другие подписчики (например, дашборды) могут реагировать на агрегированные счётчики.
- `ThemeManager.theme_changed` → `IconCache` очищает кеш, Views обновляют иконки/стили.

## Зависимости

- View → ViewModel: связаны через сигналы/слоты и `ViewModelFactory` (`src/viewmodels/factory.py`).
- ViewModel → Model: обращаются к `SerialWorker`, `ConfigLoader`, `QuickBlocksRepository` (через `service_container`).
- Utils → Конфигурация: используют `config_defaults.ini`, YAML, файлы переводов.

## Расширение

- Добавление нового модуля отображения: создайте View + ViewModel, зарегистрируйте в `ViewModelFactory`.
- Новые быстрые команды: расширьте `config/quick_blocks.yaml` или используйте диалог в UI.
- Дополнительные порты: обновите конфигурацию в `config.ini` (раздел `ports`).
