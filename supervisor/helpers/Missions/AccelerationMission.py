from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.CommunicationLayer import CommunicationLayer


class AccelerationMission(MissionFinishing):

    def __init__(self, communication):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Call super().__init__(communication, MissionType.ACCELERATION).
                 Initialize targetDistance (hardcoded).
                 Initialize currentDistance = 0.0.
        """
        pass

    def onDistance(self, data):
        """
        Input  : data (str) — distance data from ROS topic
        Output : None
        Logic  : Parse data and update currentDistance.
                 Call checkFinish() to evaluate completion.
        """
        pass

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : If currentDistance >= targetDistance
                 call notifyMissionFinished().
        """
        pass