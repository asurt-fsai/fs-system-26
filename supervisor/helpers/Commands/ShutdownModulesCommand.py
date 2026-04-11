from supervisor.helpers.Commands import Command

class ShutdownModulesCommand(Command):

    def __init__(self, moduleManager, logger):
        self.moduleManager = moduleManager
        self.logger = logger

    def execute(self):

        self.logger.warning("Shutting down all modules")

        self.moduleManager.shutdownAllModules()
