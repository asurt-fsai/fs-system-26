from supervisor.helpers.Missions.MissionFinishing import MissionFinishing



class AutocrossMission(MissionFinishing):

    def __init__(self, communication):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : 
                 Initialize orangeConeDetected = False.
                 Initialize loopClosureDetected = False.
        """
        pass

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Set orangeConeDetected = True.
                 Call checkFinish().
        """
        pass

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Set loopClosureDetected = True.
                 Call checkFinish().
        """
        pass

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If both orangeConeDetected and loopClosureDetected are True
                 call notifyMissionFinished().
        """
        pass