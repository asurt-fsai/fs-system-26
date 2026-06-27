from supervisor.helpers.Commands.Command import Command
class EmergencyStopCommand(Command):

    def __init__(self, mission_manager_client, module_manager_client, logger):
        self.mission_manager_client = mission_manager_client
        self.module_manager_client = module_manager_client
        self.logger = logger

    def execute(self):

        self.logger.critical("EMERGENCY STOP triggered")

        # Attempt to stop mission first
        try:
            self.mission_manager_client.stop_mission()
            self.module_manager_client.shutdown_all()
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}", exc_info=True)