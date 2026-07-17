from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType

class SkidpadMission(MissionFinishing):
    MissionType=MissionType.SKIDPAD
    
    def __init__(self, communication, supervisor):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Initialize skidpadFinished = False.
        """
        super().__init__(communication, supervisor)
        self.skidpadFinished = False
        self.targetDistance = 280
        self.currentDistance = 0.0

    def onLoopClosure(self, data):
        """
        Input  : data — loop closure data from ROS topic
        Output : None
        Logic  : Mark skidpadFinished = True.s
                 Call checkFinish().
        """
        if data:
            self.logger.info("[SKIDPAD] Loop closure detected")
            self.skidpadFinished = False
            self.checkFinish()

    def onConeDetected(self, data):
        """
        Input  : data — orange cone detection data from ROS topic
        Output : None
        Logic  : Mark skidpadFinished = True.
                 Call checkFinish().
        """
        if data:
            self.logger.info("[SKIDPAD] Orange cone detected")
            self.skidpadFinished = False
            self.checkFinish()

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
        Logic  : If skidpadFinished is True
                 call notifyMissionFinished().
        """
        if self.missionStatus == MissionStatus.FINISHED:
            return

        if (self.currentDistance >= self.targetDistance):
            self.logger.info("🏁 distance reached in SKIDPAD mission")
            self.notifyMissionFinished()