# Code Audit Report: Modern-UART_CTRL

**Date:** 2026-02-18  
**Project:** Modern-UART_CTRL (PyQt6 Serial Port Controller)  
**Overall Score:** 6.5/10  

---

## Executive Summary

Код представляет собой функциональное приложение с четкой MVVM-архитектурой на PyQt6. Однако код содержит значительные области для улучшения: избыточные конструкции, непоследовательный Pythonic style, смешение языков в комментариях, дублирование кода и антипаттерны. После рефакторинга потенциальный рейтинг: 8.5/10.

---

## 📊 Scoring Breakdown

| Category | Score | Notes |
|----------|-------|-------|
| Code Aesthetics | 5/10 | Избыточная вложенность, дублирование |
| Pythonic Style | 6/10 | Непоследовательное использование idioms |
| Naming Quality | 7/10 | В основном хорошее, но есть исключения |
| Maintainability | 6/10 | Дублирование кода снижает maintainability |
| Performance | 8/10 | Efficient use of deque, caching |
| Documentation | 5/10 | Смешение языков, избыточные комментарии |

---

## 🎯 Priority Action Plan

### PHASE 1: Critical (High Impact, Low Effort)

#### 1.1 Eliminate Duplicate `_normalize_state` Function ✅ DONE
**Files:** `com_port_viewmodel.py`, `port_panel_view.py`  
**Impact:** High - eliminates code duplication

*Status:* Completed - function removed from both files, now using centralized `normalize_state` from `state_utils.py`

```python
# NEW FILE: src/utils/state_utils.py (or add to existing)

def normalize_connection_state(
    state: str | "PortConnectionState"
) -> "PortConnectionState":
    """
    Normalize connection state to PortConnectionState enum.
    
    Args:
        state: State as string or enum
        
    Returns:
        PortConnectionState enum member
    """
    from src.utils.state_utils import PortConnectionState
    
    if isinstance(state, PortConnectionState):
        return state
    
    if isinstance(state, str):
        candidate = state.split('.')[-1].lower()
        for option in PortConnectionState:
            if option.value == candidate or option.name.lower() == candidate:
                return option
    
    return PortConnectionState.DISCONNECTED
```

#### 1.2 Fix Duplicate Import ✅ DONE
**File:** `src/utils/icon_cache.py`, line 22-23  

*Status:* Completed - duplicate import removed

```python
# BEFORE:
from src.utils.paths import get_root_dir
from src.utils.paths import get_root_dir  # Duplicate!

# AFTER:
from src.utils.paths import get_root_dir
```

#### 1.3 Replace `.format()` with f-strings ✅ DONE
**Files:** `serial_worker.py`, `com_port_viewmodel.py`, `main_window.py`, `command_history_dialog.py`  

*Status:* Completed - all `.format()` replaced with f-strings in src/ directory

```python
# BEFORE:
"Worker error ({port}): {error}".format(port=port_name, error=error)

# AFTER:
f"Worker error ({port_name}): {error}"
```

#### 1.4 Fix Redundant Icon Assignment ✅ DONE
**File:** `src/views/console_panel_view.py`  

*Status:* Completed - replaced if-elif chain with dictionary lookup in `_create_log_tabs()` and `_update_tab_icons()`

```python
# BEFORE:
if port_label == "CPU1":
    self._tab_widget.setTabIcon(tab_index, get_icon("paper-plane"))
elif port_label == "CPU2":
    self._tab_widget.setTabIcon(tab_index, get_icon("paper-plane"))  # Duplicate!
elif port_label == "TLM":
    self._tab_widget.setTabIcon(tab_index, get_icon("magnifying-glass"))

# AFTER:
icon_map = {"CPU1": "paper-plane", "CPU2": "paper-plane", "TLM": "magnifying-glass"}
if port_label in icon_map:
    self._tab_widget.setTabIcon(tab_index, get_icon(icon_map[port_label]))
```

---

### PHASE 2: Important (Medium Impact, Medium Effort)

#### 2.1 Reduce Nested Conditionals ✅ DONE
**File:** `src/views/console_panel_view.py` - `DropableTextEdit` class  

*Status:* Completed - refactored deeply nested conditionals (4+ levels) into helper methods

**Before:**
```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.endswith(('.txt', '.log', '.hex', '.bin', '.csv')):
                    event.acceptProposedAction()
                    return
    elif event.mimeData().hasText():
        event.acceptProposedAction()
```

**After:**
```python
EXTENSIONS = ('.txt', '.log', '.hex', '.bin', '.csv')

def dragEnterEvent(self, event):
    mime = event.mimeData()
    
    if mime.hasUrls() and any(
        url.isLocalFile() and url.toLocalFile().endswith(EXTENSIONS)
        for url in mime.urls()
    ):
        event.acceptProposedAction()
    elif mime.hasText():
        event.acceptProposedAction()
```

#### 2.2 Improve Ternary Logic ✅ DONE
**File:** `src/utils/config_loader.py`  

*Status:* Completed - replaced non-Pythonic ternary with `.get()` in 3 places

```python
# BEFORE:
defaults = self._default_colors["dark" if theme not in self._default_colors else theme]

# AFTER:
defaults = self._default_colors.get(theme, self._default_colors["dark"])
```

#### 2.3 Remove Redundant Lambda Functions ✅ DONE
**File:** `src/utils/config_loader.py`, lines 318, 391, 406

```python
# BEFORE:
get_int = lambda key, default: self._get_int(section, key, default)

# AFTER: Direct method calls
value = self._get_int(section, key, default)
```

*Status:* Completed - removed 3 lambda functions, replaced with direct `self._get_int(section, key, default)` calls in `get_sizes()`, `get_console_config()`, and `get_toast_config()` methods

#### 2.4 Use Modern Type Hints (Python 3.9+) ✅ DONE
**Files:** All Python files in src/

```python
# BEFORE:
from typing import Optional, Dict, List, Callable

def process(items: List[str]) -> Dict[str, int]:
    pass

# AFTER:
def process(items: list[str]) -> dict[str, int]:
    pass
```

*Status:* Completed - replaced all `Optional[X]` with `X | None`, `Dict[` with `dict[`, `List[` with `list[`, `Callable[` with `callable[` in 15+ files. Removed unused typing imports where possible.

---

### PHASE 3: Enhancement (Low Impact, High Effort)

#### 3.1 Unify Comment Language ✅ DONE
**Files:** All Python files in src/ directory (13 files modified)

#### 3.2 Add __slots__ to Simple Data Classes
```python
# BEFORE:
class LogWidget:
    def __init__(self):
        self.label = None
        self.text_edit = None

# AFTER:
class LogWidget:
    __slots__ = ('label', 'text_edit')
    
    def __init__(self):
        self.label = None
        self.text_edit = None
```

#### 3.3 Use cached_property for Expensive Computations
```python
# BEFORE:
def get_colors(self):
    if not hasattr(self, '_colors'):
        self._colors = self._compute_colors()
    return self._colors

# AFTER:
@cached_property
def colors(self):
    return self._compute_colors()
```

#### 3.4 Replace Mutable Default Arguments
```python
# BEFORE:
def __init__(self, config: dict = {}):

# AFTER:
def __init__(self, config: dict | None = None):
    config = config or {}
```

---

## 📋 File-Specific Issues

### src/utils/icon_cache.py
- [ ] Line 22-23: Duplicate import `get_root_dir`
- [ ] Excessive defensive null checks
- [ ] Mixed use of os.path and pathlib

### src/utils/theme_manager.py
- [ ] Line 248: Non-Pythonic ternary
- [ ] Excessive comments in Russian

### src/views/console_panel_view.py
- [ ] Lines 38-75: Deeply nested conditionals
- [ ] Incomplete `dropEvent` method (line 55)
- [ ] Inconsistent type hints

### src/views/main_window.py
- [ ] Lines 334-339: Redundant icon assignment
- [ ] Lines 390-410: Lambda overuse in signal connections

### src/models/serial_worker.py
- [ ] Multiple `.format()` calls should be f-strings
- [ ] Verbose property definitions

### src/viewmodels/com_port_viewmodel.py
- [ ] Duplicate `_normalize_state` method
- [ ] String concatenation `command + '\r\n'`

### src/utils/config_loader.py
- [ ] Redundant lambda functions
- [ ] Can use dataclasses more effectively
