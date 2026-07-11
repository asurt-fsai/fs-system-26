from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.mission_types import MissionType

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
        self.targetDistance = 80.0
        self.currentDistance = 0.0
        self.orangeConeDetected = False

        self.orangeConeDistance = None
        self.ORANGE_CONE_FINISH_DISTANCE = 6  # meters

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
            distance_since_orange = (
                self.currentDistance - self.orangeConeDistance
            )
            
            if (self.currentDistance >= self.targetDistance) and self.orangeConeDetected and (distance_since_orange >= self.ORANGE_CONE_FINISH_DISTANCE):
                self.logger.info("🏁 distance reached in acceleration mission")
                self.notifyMissionFinished()

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Handle cone detection event.
        """
        if data:
            self.orangeConeDetected = True
            self.logger.info("[ACCELERATION] Orange cone detected")
            self.orangeConeDistance = self.currentDistance
            self.checkFinish()