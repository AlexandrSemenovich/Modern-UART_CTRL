# Аудит локализации Modern UART Control

Документ фиксирует текущее состояние перевода UI и перечисляет шаги для полного покрытия всех экранов. Критерии: все статические тексты должны использовать `tr()` из [`python.src.utils.translator`](src/utils/translator.py:1), а каждое окно обязано реагировать на `translator.language_changed`.

## 1. Главный экран (MainWindow)
- **Файлы**: [`python.src.views.main_window`](src/views/main_window.py:1), [`python.src.views.port_panel_view`](src/views/port_panel_view.py:1).
- **Проблемы**:
  - Секции правой панели (счётчики, секундомер) частично переводятся. Нужно централизовать `_update_stopwatch_group_title()` и убедиться, что `_stopwatch_status_label` и `_stopwatch_group` получают строки из `tr()` при старте и при `_on_language_changed`.
  - Некоторые кнопки в `_create_command_group()` ещё создаются с жёсткими строками (например, `QMessageBox` текст подтверждения) — проверить.
- **Действия**:
  1. В `_on_language_changed` дополнительно обновлять `status_bar` сообщения и `QGroupBox` заголовки (`data_transmission`, `port_counters`, `stopwatch`).
  2. Проверить подсказки (`setToolTip`) и `AccessibleName` всех кнопок.

## 2. Диалог истории команд
- **Файл**: [`python.src.views.command_history_dialog`](src/views/command_history_dialog.py:1).
- **Проблемы**: Toolbar-иконки используют `act.setText(...)`, но видно, что tooltips устанавливаются один раз; нужно обновлять их в `_on_language_changed`.
- **Действия**: добавить метод `retranslate_ui`, который проходит по actions (`_act_send` и т.д.) и переустанавливает `.setText()` и `.setToolTip()`.

## 3. Панель портов (PortPanelView)
- **Файл**: [`python.src.views.port_panel_view`](src/views/port_panel_view.py:1).
- **Проблема**: подключение к `translator.language_changed` есть, но необходимо проверить блоки `QMessageBox` и текстовые статусы (Connected/Disconnected). Убедиться, что `QAction` и подсказки обновляются.

## 4. Панель консоли (ConsolePanelView)
- **Файл**: [`python.src.views.console_panel_view`](src/views/console_panel_view.py:1).
- **Проблемы**: часть placeholder'ов и кнопок toolbar генерируются один раз. Нужно добавить `retranslate_ui()` для всех `QAction` (`Find`, `Save`, `Clear`).

## 5. Панель быстрых блоков
- **Файлы**: [`python.src.views.quick_blocks_panel`](src/views/quick_blocks_panel.py:1), [`python.src.views.quick_block_editor_dialog`](src/views/quick_block_editor_dialog.py:1).
- **Проблемы**: подписи карточек и меню редактирования. Проверить вызов `tr()` для названий блоков, кнопок «Добавить/Удалить», диалогов подтверждения.

## 6. Диалог секундомера (StopwatchWindow)
- **Файл**: [`python.src.views.stopwatch_window`](src/views/stopwatch_window.py:1).
- **Проблемы**: окно использует `StopwatchWidget`, но само название и `toolTip` окна нужно обновлять при смене языка (подписаться на `translator.language_changed`).

## 7. Виджет секундомера
- **Файл**: [`python.src.views.widgets.stopwatch_widget`](src/views/widgets/stopwatch_widget.py:1).
- **Проблемы**: кнопки уже используют `tr`, но требуется отписка от `translator.language_changed` при удалении (во избежание утечек). Добавить `def cleanup()` или переопределить `event` с `QEvent.LanguageChange`.

## 8. Диалог быстрых команд (QuickBlockEditor)
- **Файл**: [`python.src/views/quick_block_editor_dialog`](src/views/quick_block_editor_dialog.py:1).
- **Проблемы**: формы полей (`QLineEdit` placeholders) жёстко прописаны. Добавить метод `retranslate_ui()` и вызывать при `language_changed`.

## 9. SplashScreen и окна загрузки
- **Файл**: [`python.src/views/splash_screen`](src/views/splash_screen.py:1).
- **Действия**: убедиться, что `setWindowTitle`, `setStatus` используют `tr()` и обновляются при смене языка (вероятно достаточно перезагрузки, но стоит проверить).

## 10. Меню и глобальные действия
- **Файл**: [`python.src/views/main_window.py`](src/views/main_window.py:932).
- **Проблемы**: `QAction` для пунктов меню создаются единожды. Нужно хранить ссылки (`self._action_stopwatch`, `self._action_save`, и т.д.) и повторно устанавливать `.setText()` внутри `_setup_menu()` или вызывать `_setup_menu()` после смены языка (уже делается, но проверить, что все строки есть в `strings.py`).

## 11. Контекстные меню портов
- **Файл**: [`python.src/views/port_panel_view.py`](src/views/port_panel_view.py:1).
- **Действия**: проверить `QMenu` для подключения/отключения, добавить `tr()` в `build_menu` и обновление при `language_changed`.

## 12. Прочие экраны
- **Quick Blocks Toolbar**, **Config диалоги**, **Log Exporter** GUI (если есть), **Настройки** (скрипты `scripts/run.py` и т.д.). Искать строки без `tr(` через: `rg -n '"[^"]*[А-Яа-яA-Za-z]' src/views` и добавить в таблицу переводов.

## 13. Процесс валидации
1. Пройти по каждому экрану, переключить язык (Ctrl+Shift+L в приложении) и убедиться, что текст обновляется без перезапуска.
2. Для новых строк добавить ключи в [`python.src.translations.strings`](src/translations/strings.py:1) и убедиться, что `en_US.py`/`ru_RU.py` генерируются автоматически.
3. Запустить `pytest tests/test_structure.py` и пользовательские тесты UI (если есть) после правок.

## 14. TODO чек-лист
- [ ] MainWindow: статусбар, правый блок, уведомления.
- [ ] ConsolePanel: тулбары и плейсхолдеры.
- [ ] QuickBlocksPanel + Editor.
- [ ] CommandHistoryDialog (toolbar + поиска).
- [ ] StopwatchWindow (подписка на language_changed).
- [ ] PortPanelView (context menus, placeholders).
- [ ] SplashScreen (тексты загрузки).
- [ ] Прочие диалоги (`QuickBlocks`, `Settings` если появятся).
