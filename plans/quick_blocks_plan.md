## Quick Blocks Architecture (File-based YAML Store)

### Goals
- Быстрый доступ к ON/OFF блокам (группы + drag-and-drop порядок)
- UI-редактор с CRUD без SQL
- Надёжное хранение на диске

### Data Layer
1. `config/quick_blocks.yaml`
   - Структура:
     ```yaml
     version: 1
     groups:
       - id: uuid
         name: "Камеры"
         collapsed: false
         blocks:
           - id: uuid
             title: "CAM 11"
             command_on: "port set 1 1"
             command_off: "port clear 1 1"
             port: "cpu1"
             order: 0
     ```
   - Сохраняем атомарно: запись во временный файл + rename.

2. `QuickBlocksRepository`
   - Загружает YAML -> in-memory модель (dataclasses `QuickGroup`, `QuickBlock`).
   - Методы: `list_groups()`, `add_block()`, `update_block()`, `remove_block()`, `reorder(group_id, new_order)`.
   - Обёрнут reader/writer lock для потокобезопасности.

3. Диапазон портов: храним перечисление (`cpu1`, `cpu2`, `tlm`, `combo`).

### UI Layer
1. **Right Panel** => Splitter → Counters + Quick Blocks Drawer.
2. **Navigation List**: `QListWidget` в режиме `IconMode`, поддержка drag-and-drop.
3. **Block Card**:
   - Label
   - Radio для выбора "default" блока (опционально)
   - Buttons `ON`, `OFF`
   - Status icon (success/error)
4. **Toolbar** над списком:
   - `Add`, `Edit`, `Delete`, `Duplicate`, `Move Up/Down`.

### Editor Dialog
Fields:
- Название (line edit)
- Группа (combobox + кнопка "новая группа")
- Порт (CPU1, CPU2, TLM, Combo)
- Команда ON (multiline)
- Команда OFF (multiline)
- Hotkey hint (опционально)
- Флаг "send_to_combo" (по умолчанию true) — при нажатии ON/OFF команда уходит на CPU1 и CPU2 параллельно.

Validation → commands не пустые, строки ≤ 1024 символа.

### Command Execution Flow
```
UI Button → QuickBlocksController.execute(block_id, mode)
  ↳ resolve port(s) via mapping (combo = CPU1+CPU2 одновременно)
  ↳ call MainWindow._send_quick_command(port_num, command)
  ↳ emit status event → updates card + toast
```

### Drag-and-drop
- События `dropEvent` → меняем порядок в in-memory → `repository.save()`.
- Группы также поддерживают reorder через контекстное меню.

### Persistence Lifecycle
1. При старте — `repository.load()`.
2. При изменении — `repository.save_atomic()`.
3. Добавить watcher для ручного "Reload" с подтверждением (перечитываем YAML).

### Next Steps
1. Реализовать YAML repository + DI (ServiceContainer).
2. Построить Quick Blocks UI.
3. Добавить Editor Dialog + drag-and-drop.
4. Обновить документацию и локализацию.
