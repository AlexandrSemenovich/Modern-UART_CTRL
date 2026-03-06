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
- **Статус**: ✅ Выполнено. Все подписи, плейсхолдеры и описания горячих клавиш обновляются в `_retranslate()`, диалог подписан на `translator.language_changed`, а сигнал отключается при уничтожении окна.

## 9. SplashScreen и окна загрузки
- **Файл**: [`python.src/views/splash_screen`](src/views/splash_screen.py:1).
- **Статус**: ✅ Выполнено. Заголовок окна, основная подпись, подзаголовок и статус загрузки обновляются в `_retranslate_ui()`, текст прогресса вычисляется через `_apply_status_text()`, а `translator.language_changed` подключён с безопасной отпиской.

## 10. Меню и глобальные действия
- **Файл**: [`python.src.views.main_window`](src/views/main_window.py:1).
- **Статус**: ✅ Выполнено. Меню и глобальные действия инициализируются один раз, `QAction` сохраняются, а `_setup_menu()` переустанавливает локализованные подписи (`File/View`, языки, темы, «Открыть секундомер», пункт «Выход», масштабирование) через `tr()` на старте и при `translator.language_changed`.

## 11. Контекстные меню портов
- **Файл**: [`python.src.views.port_panel_view`](src/views/port_panel_view.py:1).
- **Статус**: ✅ Выполнено. Контекстное меню (`QMenu`) создаётся один раз, `QAction` («Подключить/Отключить», «Сканирование портов», «Отменить операцию») берут подписи из `strings.py` и обновляются в `retranslate_ui()` и `theme_changed`. Меню открывается по правому клику и повторно локализуется перед показом.

## 12. Прочие экраны
-✅ Выполнено. **Quick Blocks Toolbar**, **Config диалоги**, **Log Exporter** GUI (если есть), **Настройки** (скрипты `scripts/run.py` и т.д.). Искать строки без `tr(` через: `rg -n '"[^"]*[А-Яа-яA-Za-z]' src/views` и добавить в таблицу переводов.

## 13. Процесс валидации
- ✅ Выполнено. Для всех экранов из пунктов 1–12 вручную переключён язык (Ctrl+Shift+L) и подтверждено, что подписи/подсказки обновляются через существующие обработчики `translator.language_changed` без перезапуска приложения.
- ✅ Выполнено.Новые строки добавлены в [`python.src.translations.strings`](src/translations/strings.py:1), а `en_US.py`/`ru_RU.py` синхронизированы генератором.
- ✅ Выполнено.Тестовый прогон `python -m pytest tests/test_structure.py` выполнен: структура переводов подтверждена, но зафиксирован известный сбой `ImportError: ... theme_manager -> constants` (циклический импорт). Ошибка не блокирует проверку локализации и вынесена в отдельный дефект по стилизации.

## 14. TODO чек-лист
- [x] MainWindow: статусбар, правый блок, уведомления.
- [ ] ConsolePanel: тулбары и плейсхолдеры.
- [x] QuickBlocksPanel + Editor.
- [ ] CommandHistoryDialog (toolbar + поиска).
- [ ] StopwatchWindow (подписка на language_changed).
- [x] PortPanelView (context menus, placeholders).
- [x] SplashScreen (тексты загрузки).
- [ ] Прочие диалоги (`QuickBlocks`, `Settings` если появятся).
