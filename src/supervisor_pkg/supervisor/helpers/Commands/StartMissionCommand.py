from supervisor.helpers.Commands.Command import Command
import logging


class StartMissionCommand(Command):

    def __init__(self, mission_manager_client, targetMission, logger=None):
        self.mission_manager_client = mission_manager_client
        self.targetMission = targetMission
        self.logger = logger or logging.getLogger(__name__)

    def execute(self):
        mission_name = getattr(self.targetMission, "name", None)
        if mission_name is None:
            mission_name = str(self.targetMission)
        self.logger.info(f"Executing StartMissionCommand: mission={mission_name}")
        self.mission_manager_client.start_mission(self.targetMission)
        self.logger.info("StartMissionCommand: mission start published")