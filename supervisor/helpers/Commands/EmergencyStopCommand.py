from supervisor.helpers.Commands import Command
from supervisor.helpers.Missions.MissionManager import MissionManager
from supervisor.helpers.Module import ModuleManager


class EmergencyStopCommand(Command):

    def __init__(self, missionManager, moduleManager, logger):
        self.missionManager = missionManager
        self.moduleManager = moduleManager
        self.logger = logger

    def execute(self):

        self.logger.critical("EMERGENCY STOP triggered")

        self.missionManager.stopMission()
        self.moduleManager.shutdownAllModules()
