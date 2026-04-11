from supervisor.helpers.Commands import Command
from supervisor.helpers.Commands import Command
from supervisor.helpers.Missions.MissionManager import MissionManager
from supervisor.helpers.Module import ModuleManager



class RestartModuleCommand(Command):

    def __init__(self, moduleManager, targetModule, logger):
        self.moduleManager = moduleManager
        self.targetModule = targetModule
        self.logger = logger

    def execute(self):

        self.logger.info(f"Restarting module: {self.targetModule}")

        self.moduleManager.restartModule(self.targetModule)
