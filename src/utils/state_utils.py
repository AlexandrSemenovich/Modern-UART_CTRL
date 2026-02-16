"""
State utilities for the application.
Provides enums and helper functions for state management.
"""

from enum import Enum
from typing import Union


class PortConnectionState(Enum):
    """Connection states for a COM port."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


def normalize_state(state: Union[str, PortConnectionState]) -> PortConnectionState:
    """
    Normalize state value to PortConnectionState enum.
    
    Args:
        state: String or PortConnectionState value
        
    Returns:
        PortConnectionState enum member
    """
    if isinstance(state, PortConnectionState):
        return state
    if isinstance(state, str):
        candidate = state.split('.')[-1].lower()
        for option in PortConnectionState:
            if option.value == candidate or option.name.lower() == candidate:
                return option
    return PortConnectionState.DISCONNECTED


def is_terminal_state(state: Union[str, PortConnectionState]) -> bool:
    """
    Check if state is terminal (no further transitions expected).
    
    Args:
        state: String or PortConnectionState value
        
    Returns:
        True if state is terminal
    """
    normalized = normalize_state(state)
    return normalized in (PortConnectionState.DISCONNECTED, PortConnectionState.ERROR)


def is_active_state(state: Union[str, PortConnectionState]) -> bool:
    """
    Check if state represents active connection.
    
    Args:
        state: String or PortConnectionState value
        
    Returns:
        True if state is active
    """
    normalized = normalize_state(state)
    return normalized == PortConnectionState.CONNECTED
