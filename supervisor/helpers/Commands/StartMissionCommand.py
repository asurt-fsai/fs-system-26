from supervisor.helpers.Commands import Command
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionManager  import MissionManager


class StartMissionCommand(Command):

    def __init__(self, missionManager,targetMission ,logger):
        self.missionManager = missionManager
        self.targetMission = targetMission
        self.logger = logger

    def execute(self):

        self.logger.info("Executing StartMissionCommand")
        self.missionManager.createMission(self.targetMission)
        self.missionManager.startMission()
