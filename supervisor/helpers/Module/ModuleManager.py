from pytest import Module, main

from supervisor.helpers.Module.LocalLuncher import LocalLauncher
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.CommunicationLayer import CommunicationLayer


class ModuleManager:

    def __init__(self):
        self.modules = []

    # ==================================================
    # Registration From MissionManager
    # ==================================================

    def registerModules(self, modules):
        """
        Register modules provided by MissionManager.
        Automatically shuts down previous mission modules.
        """

        # Shutdown old mission modules
        if self.modules:
            print("[ModuleManager] Shutting down previous mission modules...")
            self.shutdownAll()

        # Replace module list
        self.modules = list(modules)

        print(f"[ModuleManager] Registered {len(self.modules)} modules for new mission")

    # ==================================================
    # Lifecycle
    # ==================================================

    def launchAll(self):
        print("[ModuleManager] Launching mission modules...")

        failed = []

        for module in self.modules:
            try:
                module.launch()
            except Exception as e:
                print(f"[ModuleManager] Failed to launch {module.pkg}: {e}")
                failed.append(module)

        return failed

    def shutdownAll(self):
        print("[ModuleManager] Shutting down mission modules...")

        failed = []

        for module in self.modules:
            try:
                module.shutdown()
            except Exception as e:
                print(f"[ModuleManager] Failed to shutdown {module.pkg}: {e}")
                failed.append(module)

        return failed

    # ==================================================
    # Health Monitoring
    # ==================================================

    def monitorHealth(self):
        unhealthy = []

        for module in self.modules:
            try:
                module.check_health()

                if module.state in [
                    ModuleState.Error,
                    ModuleState.Unresponsive
                ]:
                    unhealthy.append(module)

            except Exception as e:
                print(f"[ModuleManager] Health check failed for {module.pkg}: {e}")
                unhealthy.append(module)

        return unhealthy

    def getModule(self, pkg: str):
        for module in self.modules:
            if module.pkg == pkg:
                return module
        return None

    def __len__(self):
        return len(self.modules)
    
