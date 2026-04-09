from supervisor.helpers.Commands import Command

class ShutdownModulesCommand(Command):

    def __init__(self, moduleManager):
        self.moduleManager = moduleManager

    def execute(self):

        print("[Command] Shutdown all modules")

        self.moduleManager.shutdownAllModules()