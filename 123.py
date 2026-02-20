import sys
from PyQt6.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout, QTabBar
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath
from PyQt6.QtCore import Qt, QRect

class ContourTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Убираем стандартную рамку, чтобы рисовать свою
        self.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab { 
                background: transparent; 
                padding: 8px 15px; 
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                font-weight: bold; 
            }
        """)

    def paintEvent(self, event):
        # Сначала вызываем стандартную отрисовку содержимого
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Настройки линии (та самая "зеленая" линия)
        pen = QPen(QColor("#2ecc71"), 2) # Зеленый цвет, толщина 2px
        painter.setPen(pen)

        # Параметры геометрии
        rect = self.rect()
        tab_bar = self.tabBar()
        index = self.currentIndex()
        
        if index < 0:
            return

        # Получаем координаты активной вкладки относительно QTabWidget
        tab_rect = tab_bar.tabRect(index)
        # Смещаем координаты, так как tabBar находится внутри TabWidget
        tab_rect.moveTopLeft(tab_bar.mapTo(self, tab_rect.topLeft()))

        # Строим путь контура
        path = QPainterPath()
        
        # Начинаем с левого нижнего угла панели
        offset = 1 # Небольшой отступ, чтобы линию не обрезало краем виджета
        
        # Левая граница и нижняя граница
        path.moveTo(rect.left() + offset, tab_rect.bottom())
        path.lineTo(rect.left() + offset, rect.bottom() - offset)
        path.lineTo(rect.right() - offset, rect.bottom() - offset)
        path.lineTo(rect.right() - offset, tab_rect.bottom())
        
        # Верхняя линия справа от вкладки
        path.lineTo(tab_rect.right(), tab_rect.bottom())
        
        # Огибаем вкладку (вверх, вправо, вниз)
        path.lineTo(tab_rect.right(), tab_rect.top() + offset)
        path.lineTo(tab_rect.left() + offset, tab_rect.top() + offset)
        path.lineTo(tab_rect.left() + offset, tab_rect.bottom())
        
        # Соединяем с началом (верхняя линия слева от вкладки)
        path.lineTo(rect.left() + offset, tab_rect.bottom())

        painter.drawPath(path)

# --- Пример использования ---
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        self.tabs = ContourTabWidget()
        self.tabs.addTab(QWidget(), "🚀 1+2")
        self.tabs.addTab(QWidget(), "🚀 CPU1")
        self.tabs.addTab(QWidget(), "🚀 CPU2")
        self.tabs.addTab(QWidget(), "🛠 TLM")

        layout.addWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())