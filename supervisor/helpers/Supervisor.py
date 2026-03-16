import time
import threading
from supervisor.helpers.Module.ModuleState import ModuleState

class Supervisor:

    def __init__(self, communication, missionManager, moduleManager, heartbeat_timeout=5.0):
        """
        Input  : communication (CommunicationLayer) — event bus
                 missionManager (MissionManager) — manages missions
                 moduleManager (ModuleManager) — manages modules directly
                 heartbeat_timeout (float) — seconds before timeout
        Output : None
        Logic  : Store all references.
                 Initialize currentState = superstate.WAITING.
                 Initialize monitor thread references.
                 Register self with communication layer.
        """
        pass

    def issueCommand(self, cmd):
        """
        Input  : cmd (Command) — any command implementing execute()
        Output : None
        Logic  : Call cmd.execute().
        """
        pass

    def transitionState(self, newState):
        """
        Input  : newState (SupervisorState) — state to transition to
        Output : None
        Logic  : Validate transition is legal.
                 Update currentState.
                 Log the transition.
                 this is the same function in old system called 'run'
        """
        pass

    def onCANState(self, data):
        """
        Input  : data (str) — CAN state data from ROS topic
        Output : None
        Logic  : Update internal asState or amiState.
                 Trigger state transitions if conditions are met.
        """
        pass

    def onVelocity(self, data):
        """
        Input  : data (str) — velocity data from ROS topic
        Output : None
        Logic  : Process velocity update.
                 Used for mission monitoring or safety checks.
        """
        pass

    def onHeartbeat(self, pkg: str):
        """
        Input  : pkg (str) — package name that sent the heartbeat
        Output : None
        Logic  : Look up module by pkg in moduleManager.
                 Update module.lastHeartbeatTime = time.time().
                 Set module.state = Running.
        """
        pass

    def checkHeartbeat(self):
        """
        Input  : None
        Output : None
        Logic  : Iterate all modules in moduleManager.
                 For each module in Running state check if
                 time.time() - lastHeartbeatTime > heartbeatTimeout.
                 If timeout exceeded issue RestartModuleCommand.
        """
        pass

    def startHeartbeatMonitor(self):
        """
        Input  : None
        Output : None
        Logic  : Start background daemon thread running _heartbeatMonitorLoop.
                 Set _monitorRunning = True.
                 Guard against starting twice.
        """
        pass

    def stopHeartbeatMonitor(self):
        """
        Input  : None
        Output : None
        Logic  : Set _monitorRunning = False.
                 Join the monitor thread with timeout.
        """
        pass

    def _heartbeatMonitorLoop(self):
        """
        Input  : None
        Output : None
        Logic  : Loop while _monitorRunning is True.
                 Call checkHeartbeat() every 1 second.
                 Catch and log any exceptions to keep thread alive.
        """
        pass

    def onMissionFinished(self, result):
        """
        Input  : result — mission result data
        Output : None
        Logic  : Transition state to FINISHED.
                 Issue ShutdownModulesCommand.
        """
        pass

    def onMissionFailed(self, reason: str):
        """
        Input  : reason (str) — why the mission failed
        Output : None
        Logic  : Transition state to STOPPING.
                 Issue EmergencyStopCommand.
                 Log the failure reason.
        """
        pass