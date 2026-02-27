"""
Process Launcher Strategy Interface
Handles actual OS process execution for a Module.
"""

from abc import ABC, abstractmethod
import subprocess
import time


class ProcessLauncher(ABC):
    """
    Abstract strategy for launching modules.
    """

    @abstractmethod
    def launch(self, module):
        pass

    @abstractmethod
    def shutdown(self, module):
        pass

    @abstractmethod
    def restart(self, module):
        pass

