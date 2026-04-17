from supervisor.helpers.Commands import Command
from supervisor.helpers.Missions.MissionManager import MissionManager


class EmergencyStopCommand(Command):

    def __init__(self, missionManager, moduleManager, logger):
        self.missionManager = missionManager
        self.moduleManager = moduleManager
        self.logger = logger

    def execute(self):

        self.logger.critical("EMERGENCY STOP triggered")

        # Attempt to stop mission first (MissionManager will shutdown modules)
        try:
            if hasattr(self.missionManager, 'stopMission'):
                self.missionManager.stopMission()
            else:
                # Fallback: directly shutdown modules
                self.moduleManager.shutdownAll()
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}", exc_info=True)