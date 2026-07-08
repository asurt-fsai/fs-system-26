from supervisor.helpers.Commands.Command import Command


class StartMissionCommand(Command):
    """Create and start a mission via the inline MissionManager."""

    def __init__(self, mission_manager, mission_type):
        self.mission_manager = mission_manager
        self.mission_type = mission_type

    def execute(self):
        self.mission_manager.createMission(self.mission_type)
        self.mission_manager.startMission()
