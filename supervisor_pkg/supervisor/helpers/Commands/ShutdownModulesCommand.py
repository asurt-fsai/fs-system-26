
from supervisor.helpers.Commands.Command import Command

class ShutdownModulesCommand(Command):

    def __init__(self, module_manager_client, logger):
        self.module_manager_client = module_manager_client
        self.logger = logger

    def execute(self):

        self.logger.warning("Shutting down all modules")
        try:
            self.module_manager_client.shutdown_all()
        except Exception as e:
            self.logger.error(f"Error shutting down modules: {e}", exc_info=True)