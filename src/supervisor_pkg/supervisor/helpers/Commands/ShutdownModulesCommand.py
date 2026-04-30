
from supervisor.helpers.Commands.Command import Command

class ShutdownModulesCommand(Command):

    def __init__(self, moduleManager, logger):
        self.moduleManager = moduleManager
        self.logger = logger

    def execute(self):

        self.logger.warning("Shutting down all modules")
        # use ModuleManager.shutdownAll()
        try:
            self.moduleManager.shutdownAll()
        except Exception as e:
            self.logger.error(f"Error shutting down modules: {e}", exc_info=True)