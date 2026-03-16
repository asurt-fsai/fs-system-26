from supervisor.helpers.Missions.MissionFinishing import MissionFinishing

class SkidpadMission(MissionFinishing):

    def __init__(self, communication):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Initialize skidpadFinished = False.
        """
        pass

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Mark skidpadFinished = True.
                 Call checkFinish().
        """
        pass

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If skidpadFinished is True
                 call notifyMissionFinished().
        """
        pass