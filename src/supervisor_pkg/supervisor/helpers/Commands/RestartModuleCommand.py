from supervisor.helpers.Commands.Command import Command


class RestartModuleCommand(Command):

    def __init__(self, module_manager_client, target_pkg, logger):
        self.module_manager_client = module_manager_client
        self.target_pkg = target_pkg
        self.logger = logger

    def execute(self):
        pkg = getattr(self.target_pkg, "pkg", str(self.target_pkg))
        self.logger.info(f"Restarting module: {pkg}")

        try:
            self.module_manager_client.restart_module(pkg)
        except Exception as e:
            self.logger.error(f"Failed to restart module {pkg}: {e}", exc_info=True)