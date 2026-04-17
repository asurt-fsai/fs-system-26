from supervisor.helpers.Module import ModuleState
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Module import Module
import time
import logging


class ModuleManager:

    def __init__(self):
        # Store modules as a dict pkg -> Module for easy lookup
        self.modules = {}
        self.logger = logging.getLogger(__name__)
        self._supervisor = None

    # ==================================================
    # Registration From MissionManager
    # ==================================================

    def registerModules(self, modules):
        """
        Input  : modules (List[Module]) — modules for the current mission
        Output : None
        Logic  : If modules already registered, shutdown all first.
                 Replace module list with new mission modules.
        """

        # Shutdown old mission modules
        if self.modules:
            self.logger.info("[ModuleManager] Shutting down previous mission modules...")
            self.shutdownAll()

        # Replace module list -> convert to dict by pkg
        self.modules = {m.pkg: m for m in modules}

        self.logger.info(f"[ModuleManager] Registered {len(self.modules)} modules for new mission")

    def setSupervisor(self, supervisor):
        """Optional: store supervisor reference for callbacks or coordination."""
        self._supervisor = supervisor
        self.logger.info("[ModuleManager] Supervisor injected")

    def getModules(self):
        """Return the internal modules mapping (pkg -> Module)."""
        return self.modules


    def launchAll(self):

        """
        Input  : None
        Output : list — modules that failed to launch
        Logic  : Launch all module in order, with a short delay between launches.
        """
        self.logger.info("[ModuleManager] Launching mission modules...")

        failed = []

        module_list = list(self.modules.values())

        for i, module in enumerate(module_list):
            try:
                module.launch()
                if i < len(module_list) - 1:  # Add delay between launches except after last
                    time.sleep(0.5)
            except Exception as e:
                self.logger.info(f"[ModuleManager] Failed to launch {module.pkg}: {e}")
                failed.append(module)

        return failed

    def shutdownAll(self):
        """
        Input  : None
        Output : list — modules that failed to shutdown
        Logic  : Iterate all modules and call module.shutdown().
                 Collect and return any modules that raised exceptions.
        """
        self.logger.info("[ModuleManager] Shutting down mission modules...")

        failed = []

        for module in list(self.modules.values()):
            try:
                module.shutdown()
            except Exception as e:
                self.logger.info(f"[ModuleManager] Failed to shutdown {module.pkg}: {e}")
                failed.append(module)

        return failed

    def getModule(self, pkg: str):
        """
        Input  : pkg (str) — package name to look up
        Output : Module or None — the matching module if found
        Logic  : Iterate modules and return first match on pkg name.
                 Return None if not found.
        """
        return self.modules.get(pkg, None)

    def __len__(self):
        """
        Input  : None
        Output : int — number of registered modules
        Logic  : Return len(self.modules).
        """
        return len(self.modules)
    
