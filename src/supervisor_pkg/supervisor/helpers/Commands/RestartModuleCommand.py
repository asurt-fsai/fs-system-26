from supervisor.helpers.Commands.Command import Command


class RestartModuleCommand(Command):

    def __init__(self, moduleManager, targetModule, logger):
        self.moduleManager = moduleManager
        self.targetModule = targetModule
        self.logger = logger

    def execute(self):

        # targetModule is a Module instance; call its restart() method
        pkg = getattr(self.targetModule, 'pkg', str(self.targetModule))
        self.logger.info(f"Restarting module: {pkg}")

        try:
            self.targetModule.restart()
        except Exception as e:
            self.logger.error(f"Failed to restart module {pkg}: {e}", exc_info=True)