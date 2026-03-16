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
        """
        Input  : module (Module) — the module to launch
        Output : bool — True if launch succeeded, False otherwise
        Logic  : Start the module's process. Update module.state to Starting.
                 Store the process reference in module.process.
        """
        pass

    @abstractmethod
    def shutdown(self, module):
        """
        Input  : module (Module) — the module to shutdown
        Output : bool — True if shutdown succeeded, False otherwise
        Logic  : Terminate the module's process and all child processes.
                 Clean up module.process reference.
        """
        pass

    @abstractmethod
    def restart(self, module):
        """
        Input  : module (Module) — the module to restart
        Output : bool — True if restart succeeded, False otherwise
        Logic  : Shutdown then launch the module.
                 Delegate entirely to shutdown() + launch().
        """
        pass

