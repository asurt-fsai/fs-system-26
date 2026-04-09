import logging
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionManager import MissionType
from abc import ABC, abstractmethod
from rclpy.node import Node
import logging


class MissionFinishing(ABC):

    def __init__(self, communication,supervisor):
        """
        Input  : communication (CommunicationLayer) — event bus
        Output : None
        Logic  : Store communication reference.
                 Initialize missionStatus = IDLE.
        """
        self.communication = communication
        self.supervisor = supervisor
        self.logger = logging.getLogger(__name__)

    @abstractmethod
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
                 Implemented by subclasses that need it.
        """
        pass

    def onLoopClosure(self, data):
        """
        Input  : data (str) — loop closure data from ROS topic
        Output : None
        Logic  : Handle loop closure event.
                 Implemented by subclasses that need it.
        """
        pass

    def onDistance(self, data):
        """
        Input  : data (str) — distance data from ROS topic
        Output : None
        Logic  : Handle distance update event.
                 Implemented by subclasses that need it.
        """
        pass

    def notifyMissionFinished(self):
        """
        Input  : None
        Output : None
        Logic  : Set missionStatus = FINISHED.
                 Notify Supervisor 
        """

        if self.missionStatus == MissionStatus.FAILED:
            return
        
        self.missionStatus = MissionStatus.FINISHED
        if self.supervisor:
            self.supervisor.onMissionFinished(self.missionStatus)
            self.logger.info(f"Mission finished with status: {self.missionStatus}")

    def notifyMissionFailed(self, reason: str):
        """
        Input  : reason (str) — description of why mission failed
        Output : None
        Logic  : Set missionStatus = FAILED.
                 Notify Supervisor with reason.
        """
        if self.missionStatus == MissionStatus.FAILED:
            return
        
        
        self.missionStatus = MissionStatus.FAILED
        if self.supervisor:
            self.supervisor.onMissionFailed(reason)
            self.logger.info(f"Mission failed : {self.missionStatus} Reason: {reason}")