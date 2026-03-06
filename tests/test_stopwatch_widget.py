from PySide6 import QtWidgets

from src.viewmodels.stopwatch_viewmodel import StopwatchViewModel
from src.views.widgets.stopwatch_widget import StopwatchWidget


def test_stopwatch_widget_initial_state(qtbot):
    vm = StopwatchViewModel()
    widget = StopwatchWidget(vm)
    qtbot.addWidget(widget)

    assert widget.findChild(QtWidgets.QLabel, "stopwatch_display") is not None
    assert widget.windowTitle() == ""
