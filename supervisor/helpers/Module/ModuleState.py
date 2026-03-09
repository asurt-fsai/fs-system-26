
"""
Module state class for node states
""" 
from enum import Enum


class ModuleState(Enum):
    """
    Enum class for the module's state:
    """
    Starting     = 0
    Ready        = 1
    Running      = 2
    Error        = 3
    Shutdown     = 4
    Unresponsive = 5
    