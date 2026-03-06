from PySide6 import QtCore

from src.viewmodels.stopwatch_viewmodel import StopwatchViewModel
from src.utils.stopwatch import StopwatchService


class DummyService(StopwatchService):
    def __init__(self):
        super().__init__()


def test_viewmodel_emits_signals(qtbot):
    service = DummyService()
    vm = StopwatchViewModel(service=service)
    emissions: list[str] = []

    def handle_time_changed(value: str) -> None:
        emissions.append(value)

    vm.time_changed.connect(handle_time_changed)

    vm.start_manual()
    qtbot.wait_until(lambda: len(emissions) > 0, timeout=500)
    vm.stop_manual()

    assert emissions
    vm.reset_manual()
    assert vm.formatted_time.startswith("00")
