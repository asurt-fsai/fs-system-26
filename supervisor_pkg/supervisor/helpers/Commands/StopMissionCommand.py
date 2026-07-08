from supervisor.helpers.Commands.Command import Command


class StopMissionCommand(Command):
    """Stop the active mission and shut down its modules."""

    def __init__(self, mission_manager):
        self.mission_manager = mission_manager

    def execute(self):
        self.mission_manager.stopMission()
