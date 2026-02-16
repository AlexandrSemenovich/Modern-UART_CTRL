#!/usr/bin/env python3
"""
Тест компактного режима с фиолетовой рамкой 20px.
Запустить: python test_compact_mode.py

ВАЖНО: Для применения стилей используйте setObjectName("compact"), а не setProperty("semanticRole", "compact")!
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QLabel
)
from PySide6.QtCore import Qt

# Настройка стилей для теста
DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}

QPushButton {
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 24px;
    min-width: 80px;
    font-weight: 500;
    qproperty-iconSize: 14px 14px;
    border: 1px solid #45475a;
    background-color: #313244;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}

/* === КОМПАКТНЫЙ РЕЖИМ (фиолетовая рамка 20px) === */
/* Используйте setObjectName("compact") для виджетов */
QPushButton#compact {
    border-radius: 4px;
    padding: 3px 10px;
    min-height: 20px;
    max-height: 20px;
    height: 20px;
    min-width: 60px;
    font-size: 11px;
    font-weight: 500;
    qproperty-iconSize: 12px 12px;
    border: 1px solid #8B5CF6;
    background-color: #313244;
    color: #cdd6f4;
}
QPushButton#compact:hover {
    background-color: rgba(139, 92, 246, 0.2);
    border-color: #7C3AED;
}
QPushButton#compact:pressed {
    background-color: rgba(139, 92, 246, 0.3);
    border-color: #6D28D9;
}

/* Компактный QLineEdit */
QLineEdit#compact {
    border-radius: 4px;
    padding: 3px 8px;
    min-height: 20px;
    max-height: 20px;
    height: 20px;
    font-size: 11px;
    border: 1px solid #8B5CF6;
    background-color: #313244;
    color: #cdd6f4;
}
QLineEdit#compact:focus {
    border: 2px solid #8B5CF6;
}

/* Компактный QComboBox */
QComboBox#compact {
    border-radius: 4px;
    padding: 3px 8px;
    min-height: 20px;
    max-height: 20px;
    height: 20px;
    font-size: 11px;
    border: 1px solid #8B5CF6;
    background-color: #313244;
    color: #cdd6f4;
}
QComboBox#compact:hover {
    border-color: #7C3AED;
}
QComboBox#compact:focus {
    border: 2px solid #8B5CF6;
}

/* Компактный QCheckBox */
QCheckBox#compact {
    spacing: 6px;
    font-size: 11px;
}
QCheckBox#compact::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #8B5CF6;
    background-color: #313244;
}
QCheckBox#compact::indicator:checked {
    background-color: #8B5CF6;
    border-color: #8B5CF6;
}
QCheckBox#compact::indicator:checked:hover {
    background-color: #A78BFA;
}
"""

def create_test_window():
    """Создать окно для тестирования компактного режима."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = QWidget()
    window.setWindowTitle("Тест компактного режима (фиолетовая рамка 20px)")
    window.setStyleSheet(DARK_STYLESHEET)
    window.resize(500, 400)
    
    layout = QVBoxLayout(window)
    layout.setSpacing(16)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Обычные элементы (24px)
    normal_label = QLabel("Обычный режим (24px):")
    layout.addWidget(normal_label)
    
    normal_layout = QHBoxLayout()
    normal_layout.setSpacing(8)
    normal_btn = QPushButton("Кнопка")
    normal_line = QLineEdit("Текстовое поле")
    normal_combo = QComboBox()
    normal_combo.addItems(["Вариант 1", "Вариант 2"])
    normal_check = QCheckBox("Чекбокс")
    normal_layout.addWidget(normal_btn)
    normal_layout.addWidget(normal_line)
    normal_layout.addWidget(normal_combo)
    normal_layout.addWidget(normal_check)
    layout.addLayout(normal_layout)
    
    # Разделитель
    layout.addSpacing(20)
    separator = QLabel("<hr>")
    separator.setStyleSheet("color: #45475a;")
    layout.addWidget(separator)
    
    # Компактные элементы (20px с фиолетовой рамкой)
    compact_label = QLabel("Компактный режим (20px, фиолетовая рамка):")
    layout.addWidget(compact_label)
    
    compact_layout = QHBoxLayout()
    compact_layout.setSpacing(8)
    
    # Кнопка с setObjectName("compact") - ПРАВИЛЬНЫЙ СПОСОБ
    compact_btn = QPushButton("Компактная")
    compact_btn.setObjectName("compact")  # <-- ПРАВИЛЬНО!
    # НЕПРАВИЛЬНО: compact_btn.setProperty("semanticRole", "compact")
    
    compact_line = QLineEdit("Поле")
    compact_line.setObjectName("compact")  # <-- ПРАВИЛЬНО!
    
    compact_combo = QComboBox()
    compact_combo.setObjectName("compact")  # <-- ПРАВИЛЬНО!
    compact_combo.addItems(["А", "Б", "В"])
    
    compact_check = QCheckBox("Выбрать")
    compact_check.setObjectName("compact")  # <-- ПРАВИЛЬНО!
    
    compact_layout.addWidget(compact_btn)
    compact_layout.addWidget(compact_line)
    compact_layout.addWidget(compact_combo)
    compact_layout.addWidget(compact_check)
    layout.addLayout(compact_layout)
    
    # Проверка высоты
    layout.addSpacing(20)
    check_label = QLabel("Проверка высоты:")
    layout.addWidget(check_label)
    
    check_layout = QHBoxLayout()
    
    # Создаём тестовые виджеты для измерения
    test_btn = QPushButton("Тест 20px")
    test_btn.setObjectName("compact")
    test_layout = QHBoxLayout()
    test_layout.addWidget(test_btn)
    layout.addLayout(test_layout)
    
    # Кнопка проверки размеров
    def check_sizes():
        print(f"=== Проверка размеров ===")
        print(f"Обычная кнопка: minHeight={normal_btn.minimumHeight()}, sizeHint={normal_btn.sizeHint().height()}")
        print(f"Компактная кнопка: minHeight={compact_btn.minimumHeight()}, sizeHint={compact_btn.sizeHint().height()}")
        print(f"Обычный QLineEdit: {normal_line.minimumHeight()}")
        print(f"Компактный QLineEdit: {compact_line.minimumHeight()}")
        print(f"Обычный QComboBox: {normal_combo.minimumHeight()}")
        print(f"Компактный QComboBox: {compact_combo.minimumHeight()}")
        
        # Принудительно устанавливаем фиксированный размер для компактных
        compact_btn.setFixedHeight(20)
        compact_line.setFixedHeight(20)
        compact_combo.setFixedHeight(20)
        
        print(f"\nПосле setFixedHeight(20):")
        print(f"Компактная кнопка: height={compact_btn.height()}")
        print(f"Компактный QLineEdit: height={compact_line.height()}")
        print(f"Компактный QComboBox: height={compact_combo.height()}")
    
    check_btn = QPushButton("Проверить размеры в консоли")
    check_btn.setObjectName("normal")  # обычная кнопка
    check_btn.clicked.connect(check_sizes)
    layout.addWidget(check_btn)
    
    # Инструкция
    layout.addSpacing(20)
    instruction = QLabel(
        "Инструкция:\n"
        "1. Обычные элементы должны быть высотой ~24px\n"
        "2. Компактные элементы должны быть высотой 20px\n"
        "3. Фиолетовая рамка (#8B5CF6) должна быть видна\n"
        "4. Наведите на компактные элементы - рамка станет ярче\n\n"
        "ВАЖНО: Используйте setObjectName(\"compact\"), а НЕ setProperty(\"semanticRole\", \"compact\")!"
    )
    instruction.setStyleSheet("color: #a6adc8; font-size: 11px;")
    layout.addWidget(instruction)
    
    return window

if __name__ == "__main__":
    window = create_test_window()
    window.show()
    sys.exit(QApplication.exec())
