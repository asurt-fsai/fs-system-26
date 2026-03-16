from supervisor.helpers.CommunicationLayer import CommunicationLayer



class MissionFinishing:

    def __init__(self, communication):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Store communication reference.
                 Initialize missionStatus = IDLE.
        """
        pass

    def checkFinish(self):
        """
        Input  : None
        Output : None
        Logic  : Check mission-specific finish conditions.
                 If finished call notifyMissionFinished().
                 If failed call notifyMissionFailed with reason.
                 Must be implemented by each subclass.
        """
        pass

    def onConeDetected(self, data):
        """
        Input  : data (str) — cone detection data from ROS topic
        Output : None
        Logic  : Handle cone detection event.
                 Update relevant mission state.
                 Implemented by subclasses that need it.
        """
        pass

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Handle loop closure event.
                 Update relevant mission state.
                 Implemented by subclasses that need it.
        """
        pass

    def onDistance(self, data):
        """
        Input  : data (str) — distance data from ROS topic
        Output : None
        Logic  : Handle distance update event.
                 Update relevant mission state.
                 Implemented by subclasses that need it.
        """
        pass

    def notifyMissionFinished(self):
        """
        Input  : None
        Output : None
        Logic  : Set missionStatus = FINISHED.
                 Notify Supervisor via communication layer.
        """
        pass

    def notifyMissionFailed(self, reason: str):
        """
        Input  : reason (str) — description of why mission failed
        Output : None
        Logic  : Set missionStatus = FAILED.
                 Notify Supervisor via communication layer with reason.
        """
        pass