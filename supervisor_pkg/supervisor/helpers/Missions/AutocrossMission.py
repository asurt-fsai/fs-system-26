from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.mission_types import MissionType
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
        self.loopClosureDistance = None
        self.LOOP_CLOSURE_FINISH_DISTANCE = 12 # meters

        self.currentDistance = 0.0

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
            self.loopClosureDistance = self.currentDistance
            self.logger.info("[AUTOCROSS] Loop closure detected")
            self.checkFinish()

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If either orangeConeDetected or loopClosureDetected is True
                 call notifyMissionFinished().
        """
        if self.missionStatus == MissionStatus.FINISHED:
            return

        # if self.orangeConeDetected or self.loopClosureDetected:
        #     self.logger.info("[AUTOCROSS]🏁 Autocross mission finished")
        #     self.notifyMissionFinished()

         # Loop closure requires +5 m travel
        if self.loopClosureDetected and self.orangeConeDetected:
            distance_since_loop = (
                self.currentDistance - self.loopClosureDistance
            )

            if distance_since_loop >= self.LOOP_CLOSURE_FINISH_DISTANCE:
                self.logger.info(
                    f"[AUTOCROSS] Traveled "
                    f"{distance_since_loop:.2f} m after loop closure"
                )
                self.logger.info("[AUTOCROSS] 🏁 Autocross mission finished")
                self.notifyMissionFinished()

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