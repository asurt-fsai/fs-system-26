from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType

class TrackdriveMission(MissionFinishing):
    missionType = MissionType.TRACKDRIVE

    def __init__(self, communication,supervisor):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : 
                 Initialize loopClosureCount = 0.
                 Initialize orangeConeCount = 0.
                 Define required loop closures and orange cone thresholds (hardcoded).
        """
        super().__init__(communication,supervisor)
        self.loopClosureCount = 0
        self.orangeConeCount = 0
        self.requiredLoopClosures = 10 #nefteker ne3mlhom 10  
        self.requiredOrangeCones = 10  #nefteker ne3mlhom 10
        self.loopClosureDistance = None
        self.LOOP_CLOSURE_FINISH_DISTANCE = 12  # meters

        self.currentDistance = 0.0


    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Increment loopClosureCount.
                 Call checkFinish().
        """
        if data:
            self.loopClosureCount += 1
            self.logger.info(f"[TRACKDRIVE] Loop closure count: {self.loopClosureCount}/{self.requiredLoopClosures}")
            #if self.loopClosureCount == self.requiredLoopClosures:
            self.loopClosureDistance = self.currentDistance
            self.logger.info(f"[TRACKDRIVE] Loop closure distance recorded: {self.loopClosureDistance:.2f} m")
            self.checkFinish()

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Increment orangeConeCount.
                 Call checkFinish().
        """
        if data:
            self.orangeConeCount += 1
            self.logger.info(f"[TRACKDRIVE] Orange cone count: {self.orangeConeCount}/{self.requiredOrangeCones}")
            self.checkFinish()

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If loopClosureCount >= required threshold
                 AND orangeConeCount >= required threshold
                 call notifyMissionFinished().
        """
        if self.missionStatus == MissionStatus.FINISHED:
            return

        if (self.loopClosureCount >= self.requiredLoopClosures and
                self.orangeConeCount >= self.requiredOrangeCones):
            
            distance_since_loop = (
                self.currentDistance - self.loopClosureDistance
            )

            if distance_since_loop >= self.LOOP_CLOSURE_FINISH_DISTANCE:
                self.logger.info(
                    f"[TRACKDRIVE] Traveled "
                    f"{distance_since_loop:.2f} m after loop closure"
                )
                self.logger.info("🏁 Trackdrive mission complete!")
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