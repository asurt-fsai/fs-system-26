from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Module.Module import Module
import time


class ModuleManager:

    def __init__(self):
        self.modules = []

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
            print("[ModuleManager] Shutting down previous mission modules...")
            self.shutdownAll()

        # Replace module list
        self.modules = list(modules)

        print(f"[ModuleManager] Registered {len(self.modules)} modules for new mission")


    def launchAll(self):

        """
        Input  : None
        Output : list — modules that failed to launch
        Logic  : Launch all module in order, with a short delay between launches.
        """
        print("[ModuleManager] Launching mission modules...")

        failed = []

        for i, module in enumerate(self.modules):
            try:
                module.launch()
                if i < len(self.modules) - 1:  # Add delay between launches except after last
                    
                    time.sleep(0.5)
            except Exception as e:
                print(f"[ModuleManager] Failed to launch {module.pkg}: {e}")
                failed.append(module)

        return failed

    def shutdownAll(self):
        """
        Input  : None
        Output : list — modules that failed to shutdown
        Logic  : Iterate all modules and call module.shutdown().
                 Collect and return any modules that raised exceptions.
        """
        print("[ModuleManager] Shutting down mission modules...")

        failed = []

        for module in self.modules:
            try:
                module.shutdown()
            except Exception as e:
                print(f"[ModuleManager] Failed to shutdown {module.pkg}: {e}")
                failed.append(module)

        return failed

    def getModule(self, pkg: str):
        """
        Input  : pkg (str) — package name to look up
        Output : Module or None — the matching module if found
        Logic  : Iterate modules and return first match on pkg name.
                 Return None if not found.
        """
        for module in self.modules:
            if module.pkg == pkg:
                return module
        return None

    def __len__(self):
        """
        Input  : None
        Output : int — number of registered modules
        Logic  : Return len(self.modules).
        """
        return len(self.modules)
    
