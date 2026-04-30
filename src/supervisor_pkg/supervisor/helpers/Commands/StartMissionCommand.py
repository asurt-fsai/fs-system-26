from supervisor.helpers.Commands.Command import Command
import logging


class StartMissionCommand(Command):

    def __init__(self, missionManager, targetMission, logger=None):
        self.missionManager = missionManager
        self.targetMission = targetMission
        self.logger = logger or logging.getLogger(__name__)

    def execute(self):

        self.logger.info("Executing StartMissionCommand")
        self.missionManager.createMission(self.targetMission)
        self.missionManager.startMission()