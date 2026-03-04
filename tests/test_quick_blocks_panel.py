import pytest
from PySide6 import QtWidgets

from src.views.quick_blocks_panel import QuickBlocksPanel
from src.utils.quick_blocks_repository import QuickBlocksRepository


class DummyRepository(QuickBlocksRepository):
    def __init__(self):
        super().__init__(None)


@pytest.fixture
def panel(qtbot):
    repo = DummyRepository()
    widget = QuickBlocksPanel(repo)
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_toolbar_labels_update_on_resize(panel, qtbot):
    panel.resize(1400, 800)
    qtbot.wait(10)
    assert panel._btn_add.text()


