from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionManager import MissionType

class AccelerationMission(MissionFinishing):
    missionType = MissionType.ACCELERATION
    def __init__(self, communication,supervisor):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Call super().__init__(communication, MissionType.ACCELERATION).
                 Initialize targetDistance (hardcoded).
                 Initialize currentDistance = 0.0.
        """
        super().__init__(communication,supervisor)
        self.targetDistance = 75.0
        self.currentDistance = 0.0

    def onDistance(self, data):
        """
        Input  : data (str) — distance data from ROS topic
        Output : None
        Logic  : Parse data and update currentDistance.
                 Call checkFinish() to evaluate completion.
        """
        try:
            self.currentDistance = float(data)

            self.logger.info(f"Distance = {self.currentDistance}")

            self.checkFinish()

        except Exception as e:
            self.logger.info("Invalid distance ignored")
            return

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If currentDistance >= targetDistance
                 call notifyMissionFinished().
        """
        if self.missionStatus != MissionStatus.FINISHED:
            if self.currentDistance >= self.targetDistance:
                self.logger.info("🏁 distance reached in acceleration mission")
                self.notifyMissionFinished()

