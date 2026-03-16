from supervisor.helpers.Missions.MissionFinishing import MissionFinishing


class TrackdriveMission(MissionFinishing):

    def __init__(self, communication):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : 
                 Initialize loopClosureCount = 0.
                 Initialize orangeConeCount = 0.
                 Define required loop closures and orange cone thresholds (hardcoded).
        """
        pass

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Increment loopClosureCount.
                 Call checkFinish().
        """
        pass

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Increment orangeConeCount.
                 Call checkFinish().
        """
        pass

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If loopClosureCount >= required threshold
                 AND orangeConeCount >= required threshold
                 call notifyMissionFinished().
        """
        pass