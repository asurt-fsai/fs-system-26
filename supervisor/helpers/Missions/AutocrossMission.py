from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionManager import MissionType
class AutocrossMission(MissionFinishing):
    missionType = MissionType.AUTOCROSS
    def __init__(self, communication,supervisor):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : 
                 Initialize orangeConeDetected = False.
                 Initialize loopClosureDetected = False.
        """
        super().__init__(communication, supervisor)
        self.orangeConeDetected = False
        self.loopClosureDetected = False

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Handle cone detection event.
        """
        if data:
            self.orangeConeDetected = True
            self.logger.info("[AUTOCROSS] Orange cone detected")
            self.checkFinish()

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Handle loop closure event.
        """
        if data:
            self.loopClosureDetected = True
            self.logger.info("[AUTOCROSS] Loop closure detected")
            self.checkFinish()

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If both orangeConeDetected and loopClosureDetected are True
                 call notifyMissionFinished().
        """
        if self.missionStatus == MissionStatus.FINISHED:
            return

        if self.orangeConeDetected and self.loopClosureDetected:
            self.logger.info("[AUTOCROSS]🏁 Autocross mission finished")
            self.notifyMissionFinished()