"""
Final Validation Script - moved to tests/
"""

import sys

def test_imports():
    from src.models.base_model import BaseModel
    assert BaseModel is not None

def test_models():
    from src.models.com_port_model import ComPortModel
    m = ComPortModel()
    m.port_name = 'COM1'
    assert m.port_name == 'COM1'

def test_viewmodel():
    from src.viewmodels.com_port_viewmodel import ComPortViewModel
    from src.models.com_port_model import ComPortModel
    vm = ComPortViewModel(ComPortModel())
    assert hasattr(vm, 'is_connected')
