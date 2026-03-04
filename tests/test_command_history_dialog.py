import pytest

from src.viewmodels.command_history_viewmodel import CommandHistoryModel
from src.views.command_history_dialog import CommandHistoryDialog


@pytest.fixture
def history_model(tmp_path, monkeypatch):
    monkeypatch.setenv("UART_CTRL_CONFIG_DIR", str(tmp_path))
    model = CommandHistoryModel()
    model.clear()
    model.add_entry("PING TEST", "CPU1")
    model.add_entry("HELLO", "CPU2")
    return model


def test_history_search_filters_rows(history_model, qtbot):
    dialog = CommandHistoryDialog(history_model)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog._search.setText("ping")
    qtbot.wait(50)

    assert dialog._proxy_model.rowCount() == 1
    assert dialog._highlight_delegate.pattern is not None
    assert dialog._lbl_search_results.isVisible()
    assert dialog._search.property("hasMatches") is True


def test_history_search_clear_resets_feedback(history_model, qtbot):
    dialog = CommandHistoryDialog(history_model)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog._search.setText("missing")
    qtbot.wait(50)
    assert dialog._proxy_model.rowCount() == 0
    assert dialog._lbl_search_results.isVisible()
    assert dialog._search.property("hasMatches") is False

    dialog._search.setText("")
    qtbot.wait(30)
    assert dialog._lbl_search_results.isVisible() is False
    assert dialog._highlight_delegate.pattern is None
