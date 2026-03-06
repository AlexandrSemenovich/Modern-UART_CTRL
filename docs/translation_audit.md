# Аудит локализации Modern UART Control

Документ фиксирует текущее состояние перевода UI и перечисляет шаги для полного покрытия всех экранов. Критерии: все статические тексты должны использовать `tr()` из [`python.src.utils.translator`](src/utils/translator.py:1), а каждое окно обязано реагировать на `translator.language_changed`.

## 1. Главный экран (MainWindow)
- **Файлы**: [`python.src.views.main_window`](src/views/main_window.py:1), [`python.src.views.port_panel_view`](src/views/port_panel_view.py:1).
- **Статус**: ✅ Выполнено. Переводы для командной панели и секундомера подключены, но блок «Счётчики портов» обновляется вручную и не реагирует на `translator.language_changed`. Требуется вынести тексты RX/TX/Errors/Time и заголовок группы в отдельные методы и вызывать их при старте/смене языка. После рефакторинга обновить документацию.

## 2. Диалог истории команд
- **Файлы**: [`python.src.views.command_history_dialog`](src/views/command_history_dialog.py:1), [`python.src.viewmodels.command_history_viewmodel`](src/viewmodels/command_history_viewmodel.py:1).
- **Статус**: ✅ Выполнено. Заголовки столбцов и статусы строк берут переводы из `strings.py`, тулбар и подсказки обновляются при смене языка.

## 3. Панель портов (PortPanelView)
- **Файл**: [`python.src.views.port_panel_view`](src/views/port_panel_view.py:1).
- **Статус**: ✅ Выполнено. Все статические строки проходят через `tr()`, кнопки/подписи обновляются в `retranslate_ui()`, `translator.language_changed` подключён. Статусы «Подключение/Подключен/Отключен» используют ключи из `strings.py`, а fallback `QMessageBox` получает локализованный заголовок. Дополнительных `QAction` не используется.

## 4. Панель консоли (ConsolePanelView)
- **Файл**: [`python.src.views.console_panel_view`](src/views/console_panel_view.py:1).
- **Статус**: ✅ Выполнено. Все элементы тулбара и вкладок получают тексты через `retranslate_ui()`, обновляются placeholder'ы поисковой строки, кнопки (`Clear`, `Save`, «Регулярные выражения»), метки навигации результатов и заголовки вкладок. Тулбар реагирует на `translator.language_changed`, `QAction` в контекстном меню используют `tr()`.

## 5. Панель быстрых блоков
- **Файлы**: [`python.src.views.quick_blocks_panel`](src/views/quick_blocks_panel.py:1), [`python.src.views.quick_block_editor_dialog`](src/views/quick_block_editor_dialog.py:1).
- **Статус**: ✅ Выполнено. Тулбар панели хранит подписи в `_toolbar_labels` и пересобирает их в `_retranslate_ui()`, кнопки (`Добавить/Редактировать/Обновить`) и контекстное меню используют `tr()`. Диалог редактирования (`QuickBlockEditorDialog`) уже обновляет все поля через `_retranslate()`. Предусмотрен вызов `translator.language_changed`, а заголовки блоков/групп берутся из `strings.py`.

## 6. Диалог секундомера (StopwatchWindow)
- **Файл**: [`python.src.views.stopwatch_window`](src/views/stopwatch_window.py:1).
- **Статус**: ✅ Выполнено. Окно подписано на `translator.language_changed`, `setWindowTitle` и `setToolTip` обновляются через `tr("stopwatch_window_title")` и `tr("stopwatch_status")`, сам `StopwatchWidget` уже реагирует на смену языка.

## 7. Виджет секундомера
- **Файл**: [`python.src.views.widgets.stopwatch_widget`](src/views/widgets/stopwatch_widget.py:1).
- **Статус**: ✅ Выполнено. Виджет подключается к `translator.language_changed`, а сигнал автоматически отключается при уничтожении (через `destroyed.connect`). Кнопки обновляют подписи через `_retranslate_ui()`.

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
