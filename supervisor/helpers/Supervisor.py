import time
import threading
import logging
from enum import Enum
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Commands import ShutdownModulesCommand,StartMissionCommand,EmergencyStopCommand,RestartModuleCommand
from supervisor.helpers.Missions.MissionManager import MissionType


class SuperState(Enum):
    """
    Enum class for the supervisor's state
    """
    WAITING = 0
    LAUNCHING = 1
    READY = 2
    RUNNING = 3
    STOPPING = 4
    FINISHED = 5

class Supervisor:
        
    """
    Central orchestrator for the autonomous system.
    
    Responsibilities
    ----------------
    - State machine management (WAITING → LAUNCHING → READY → RUNNING → STOPPING → FINISHED)
    - Mission lifecycle coordination via MissionManager
    - Module health monitoring via ModuleManager
    - CAN state processing and mission type mapping
    
    Flow
    ----
    1. WAITING: Wait for AMI state (mission selection)
    2. LAUNCHING: Create mission, load and launch modules
    3. READY: Wait for AS_READY state (vehicle ready)
    4. RUNNING: Mission executing
    5. STOPPING: Mission finished, vehicle slowing down
    6. FINISHED: Shutdown modules, reset to WAITING
    """

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
        self.communication = communication
        self.missionManager = missionManager
        self.moduleManager = moduleManager
        self.heartbeat_timeout = heartbeat_timeout

        self.currentState = SuperState.WAITING
        self.logger = logging.getLogger(__name__)

        # State variables
        self.asState = None
        self.amiState = None
        self.isFinished = False
        self.currentVel = 0.0
        self.maxStopVelTh = 0.1

        # Heartbeat tracking
        self.module_last_heartbeat = {}
        self.monitor_thread = threading.Thread(target=self._heartbeat_monitor_loop, daemon=True)
        self.monitor_thread.start()

        # Register with managers
        self.communication.registerSupervisor(self)
        self.missionManager.setSupervisor(self)
        self.moduleManager.setSupervisor(self)  # If ModuleManager needs it
        self.logger.info("[Supervisor] Initialized in WAITING state")


    def issueCommand(self, cmd):
        """
        Input  : cmd (Command) — any command implementing execute()
        Output : None
        Logic  : Call cmd.execute().
        """
        try:
            cmd_name = type(cmd).__name__
            self.logger.info(f"[Supervisor] Issuing command: {cmd_name}")
            cmd.execute()
            self.logger.info(f"[Supervisor] Command executed: {cmd_name}")
        except Exception as e:
            self.logger.error(f"[Supervisor] Failed to execute command {type(cmd).__name__}: {e}", exc_info=True)



    # ========================
    # STATE TRANSITIONS
    # ========================
    def transitionState(self, newState):
        """
        Input  : newState (SupervisorState) — state to transition to
        Output : None
        Logic  : Validate transition is legal.
                 Update currentState.
                 Log the transition.
                 this is the same function in old system called 'run'
        """
        # Auto transition if newState is None
        state = newState if newState else self.currentState

        if state == SuperState.WAITING:
            if self.amiState not in (None, 0):  # AMI selected
                self.currentState = SuperState.LAUNCHING
                self.logger.info("Transition to LAUNCHING")
                self.issueCommand(StartMissionCommand(self.missionManager, self.amiState))

        elif state == SuperState.LAUNCHING:
            self.currentState = SuperState.READY
            self.logger.info("Transition to READY")

        elif state == SuperState.READY:
            if self.asState == 2:  # Vehicle ready to run
                self.currentState = SuperState.RUNNING
                self.logger.info("Transition to RUNNING")

        elif state == SuperState.RUNNING:
            if self.isFinished:
                self.currentState = SuperState.STOPPING
                self.logger.info("Transition to STOPPING")

        elif state == SuperState.STOPPING:
            if self.currentVel < self.maxStopVelTh:
                self.currentState = SuperState.FINISHED
                self.logger.info("Transition to FINISHED")

        elif state == SuperState.FINISHED:
            self.issueCommand(ShutdownModulesCommand(self.moduleManager))
            self.logger.info("Mission finished. Modules shutting down.")
            time.sleep(2)  # short delay before restarting
            self.currentState = SuperState.WAITING
            self.amiState = None
            self.isFinished = False
            self.logger.info("Supervisor reset to WAITING")

    def onCANState(self, data):
        """
        Input  : data (str) — CAN state data from ROS topic
        Output : None
        Logic  : Update internal asState or amiState.
                 Trigger state transitions if conditions are met.
        """
        self.asState = data.as_state
        self.amiState = data.ami_state
        self.transitionState()  # auto-transition based on new CAN info

    def onVelocity(self, data):
        """
        Input  : data (str) — velocity data from ROS topic
        Output : None
        Logic  : Process velocity update.
                 Used for mission monitoring or safety checks.
        """
        self.currentVel = data
        # Could also check stopping conditions in STOPPING
        if self.currentState == SuperState.STOPPING:
            self.transitionState()


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

    # ========================
    # MISSION CALLBACKS
    # ========================
    def onMissionFinished(self, result):
        """
        Input  : result — mission result data
        Output : None
        Logic  : Transition state to FINISHED.
                 Issue ShutdownModulesCommand.
        """
        self.isFinished = True
        self.issueCommand(ShutdownModulesCommand(self.moduleManager))
        self.transitionState(SuperState.FINISHED)

    def onMissionFailed(self, reason: str):
        """
        Input  : reason (str) — why the mission failed
        Output : None
        Logic  : Transition state to STOPPING.
                 Issue EmergencyStopCommand.
                 Log the failure reason.
        """
        self.logger.error(f"Mission failed: {reason}")
        self.currentState = SuperState.STOPPING
        self.issueCommand(EmergencyStopCommand(self.moduleManager))