"""
Simple smoke-run: open MainWindow, wait 1s, then quit.
Used to detect runtime exceptions on startup.
"""
import sys
import os

# ensure package import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.views.main_window import MainWindow


def run():
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        app = QApplication(sys.argv)
        # apply qss if available
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'styles', 'app.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
        except Exception:
            pass

        w = MainWindow()
        w.show()

        # quit after 1 second
        QTimer.singleShot(1000, app.quit)
        rc = app.exec()
        print('SMOKE_RUN_EXIT', rc)
        return rc
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(run())
