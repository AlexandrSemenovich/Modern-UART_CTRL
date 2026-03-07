"""
ViewModels package.
"""

from src.viewmodels.main_viewmodel import MainViewModel
from src.viewmodels.com_port_viewmodel import ComPortViewModel, PortConnectionState
from src.viewmodels.factory import ViewModelFactory, get_viewmodel_factory
from src.viewmodels.protocols import (
    ComPortViewModelProtocol,
    CommandHistoryModelProtocol,
    ViewModelFactoryProtocol,
)
from src.viewmodels.widget_host_viewmodel import (
    WidgetHostViewModel,
    WidgetModuleRegistry,
    WidgetModuleDescriptor,
    ModuleDockItem,
)

__all__ = [
    'MainViewModel',
    'ComPortViewModel',
    'PortConnectionState',
    'ViewModelFactory',
    'get_viewmodel_factory',
    'ComPortViewModelProtocol',
    'CommandHistoryModelProtocol',
    'ViewModelFactoryProtocol',
    'WidgetHostViewModel',
    'WidgetModuleRegistry',
    'WidgetModuleDescriptor',
    'ModuleDockItem',
]
