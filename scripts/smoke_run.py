"""
Smoke-run script (relocated to scripts/)
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.views.main_window import MainWindow

def run():
    try:
        app = QApplication(sys.argv)
        qss_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'styles', 'app.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
        w = MainWindow()
        w.show()
        QTimer.singleShot(1000, app.quit)
        return app.exec()
    except Exception:
        import traceback
        traceback.print_exc()
        return 2

if __name__ == '__main__':
    sys.exit(run())
