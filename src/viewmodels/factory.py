"""
ViewModel Factory implementation.
Creates ViewModel instances with proper dependency injection.
"""

from typing import Optional

from src.viewmodels.com_port_viewmodel import ComPortViewModel
from src.viewmodels.command_history_viewmodel import CommandHistoryModel
from src.viewmodels.protocols import (
    ViewModelFactoryProtocol,
    ComPortViewModelProtocol,
    CommandHistoryModelProtocol,
)


class ViewModelFactory:
    """
    Factory for creating ViewModel instances.
    
    This factory follows the composition pattern, allowing easy:
    - Unit testing with mock ViewModels
    - Swapping implementations
    - Dependency injection
    
    Usage:
        factory = ViewModelFactory()
        port_vm = factory.create_port_viewmodel("COM1", 1)
        history = factory.create_history_model()
    """

    def create_port_viewmodel(
        self,
        port_label: str,
        port_number: int,
    ) -> ComPortViewModelProtocol:
        """
        Create a COM port ViewModel instance.

        Args:
            port_label: Human-readable label for the port
            port_number: Numeric identifier for the port

        Returns:
            ComPortViewModel instance
        """
        return ComPortViewModel(port_label, port_number)

    def create_history_model(
        self,
        parent: Optional[object] = None,
    ) -> CommandHistoryModelProtocol:
        """
        Create a command history model instance.

        Args:
            parent: Optional parent object

        Returns:
            CommandHistoryModel instance
        """
        return CommandHistoryModel(parent=parent)


# Singleton instance for application-wide use
_default_factory: Optional[ViewModelFactory] = None


def get_viewmodel_factory() -> ViewModelFactoryProtocol:
    """
    Get the default ViewModel factory instance.

    Returns:
        ViewModelFactory instance

    Note:
        For testing, replace with a mock factory using:
        ViewModelFactoryProtocol = mock.Mock(spec=ComPortViewModelProtocol)
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = ViewModelFactory()
    return _default_factory


def set_viewmodel_factory(factory: ViewModelFactoryProtocol) -> None:
    """
    Set a custom ViewModel factory.

    Args:
        factory: Custom factory implementation
    """
    global _default_factory
    _default_factory = factory


__all__ = [
    "ViewModelFactory",
    "ViewModelFactoryProtocol",
    "get_viewmodel_factory",
    "set_viewmodel_factory",
]
