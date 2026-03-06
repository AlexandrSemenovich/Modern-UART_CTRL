from PySide6 import QtCore

from src.utils.stopwatch import StopwatchService, StopwatchState, format_duration


class TestStopwatchService:
    def test_format_duration_basic(self):
        assert format_duration(0) == "00 00:00:00.000"
        assert format_duration(1234) == "00 00:00:01.234"
        assert format_duration(3600_000) == "00 01:00:00.000"
        assert format_duration(86400_000) == "01 00:00:00.000"

    def test_start_stop_reset_flow(self, qtbot):
        service = StopwatchService()
        emissions: list[tuple[str, StopwatchState]] = []

        def capture(formatted: str, state: StopwatchState) -> None:
            emissions.append((formatted, state))

        service.time_changed.connect(capture)

        service.start()
        qtbot.wait_until(lambda: len(emissions) > 0, timeout=500)
        qtbot.wait(70)
        service.stop()
        assert service.state.running is False
        assert service.state.elapsed_ms >= 50

        service.reset()
        assert service.state.elapsed_ms == 0
        assert emissions[-1][1] == StopwatchState(running=False, elapsed_ms=0)

    def test_tick_emits_formatted_time(self, qtbot):
        service = StopwatchService()
        emissions: list[tuple[str, StopwatchState]] = []

        def capture(formatted: str, state: StopwatchState) -> None:
            emissions.append((formatted, state))

        service.time_changed.connect(capture)

        service.start()
        qtbot.wait_until(lambda: len(emissions) > 0, timeout=500)
        service.stop()

        assert emissions
        formatted, state = emissions[-1]
        assert isinstance(formatted, str)
        assert isinstance(state, StopwatchState)

