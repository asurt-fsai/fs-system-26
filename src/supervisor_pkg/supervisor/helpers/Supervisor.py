import time
import threading
import logging
from enum import Enum
import rclpy
from supervisor.helpers.Commands.ShutdownModulesCommand import ShutdownModulesCommand
from supervisor.helpers.Commands.EmergencyStopCommand import EmergencyStopCommand
from supervisor.helpers.Commands.RestartModuleCommand import RestartModuleCommand
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Missions.mission_types import MissionType
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.msg import CanState


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
        self.asState = CanState.AS_OFF
        self.amiState = CanState.AMI_NOT_SELECTED
        self.isFinished = False
        self.currentVel = 0.0
        self.maxStopVelTh = 0.1
        self.vel= 0.0
        self.steer =0.0

        # Heartbeat tracking: use per-module `lastHeartbeatTime` on Module instances
        # Also keep a dict of last heartbeat timestamps for quick lookup
        self.module_last_heartbeat = {}

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
    def transitionState(self):
        """
        Input  : newState (SupervisorState) — state to transition to
        Output : None
        Logic  : Validate transition is legal.
                 Update currentState.
                 Log the transition.
                 this is the same function in old system called 'run'
        """
        if self.currentState == SuperState.WAITING:
            if self.amiState != CanState.AMI_NOT_SELECTED:
                self.currentState = SuperState.LAUNCHING
                self.logger.info("[Supervisor] State transition to LAUNCHING")

        elif self.currentState == SuperState.LAUNCHING:
            self.isFinished=False
            if self.missionManager.isReady():
                self.currentState = SuperState.READY
                self.logger.info("[Supervisor] State transition to READY")

        elif self.currentState == SuperState.READY:
            if self.asState == 2:  # Vehicle ready to run
                self.currentState = SuperState.RUNNING
                self.logger.info("[Supervisor] State transition to RUNNING")

        elif self.currentState == SuperState.RUNNING:
            if self.isFinished:
                self.currentState = SuperState.STOPPING
                self.logger.info("[Supervisor] State transition to STOPPING")

        elif self.currentState == SuperState.STOPPING:
            if self.currentVel < self.maxStopVelTh:
                self.currentState = SuperState.FINISHED
                self.logger.info("[Supervisor] State transition to FINISHED")

## 3ashan n5ali el finished state yeb2a leeh timer 3ashan y3mel reset ba3d 5 seconds w ten2el lel waiting so publishing to the car the finishing state correctly 
        elif self.currentState == SuperState.FINISHED: 
            if not hasattr(self, "finished_time"):
                self.finished_time = time.time()
                self.issueCommand(ShutdownModulesCommand(self.moduleManager, self.logger))
                self.logger.info("[Supervisor] Entered FINISHED")

            elif time.time() - self.finished_time > 5:
                self.currentState = SuperState.WAITING
                self.amiState = CanState.AMI_NOT_SELECTED
                self.isFinished = False
                if hasattr(self.missionManager, "clearActiveMission"):
                    self.missionManager.clearActiveMission()
                else:
                    self.missionManager.activeMission = None
                del self.finished_time
                self.logger.info("[Supervisor] Reset to WAITING")
    

    def run(self):
        self.transitionState()
        self.publishRosCanMessages()

    #===============================
    # publishing commands to the car
    #================================
    def publishRosCanMessages(self):
        """
        Publishes control flags and commands based on current state.
        Called periodically or after state transitions.
        """
        # Publish mission and driving flags
        if self.currentState in (SuperState.WAITING, SuperState.LAUNCHING, SuperState.READY):
            self.communication.publishMissionFlag(False)
            self.communication.publishDrivingFlag(False)
        
        elif self.currentState in (SuperState.RUNNING, SuperState.STOPPING) and self.asState == 2:
            self.communication.publishMissionFlag(False)
            self.communication.publishDrivingFlag(True)
        
        elif self.currentState == SuperState.FINISHED:
            self.communication.publishMissionFlag(True)
            self.communication.publishDrivingFlag(False)
        
        # Publish drive command
        cmd_msg = self.getCmdMessage()
        self.communication.publishDriveCommand(cmd_msg)

    def getCmdMessage(self):
        """
        Generates AckermannDriveStamped command based on current state.
        
        Returns : AckermannDriveStamped message
        """
      
        
        cmdMsg = AckermannDriveStamped()
        
        if self.currentState in (
            SuperState.WAITING,
            SuperState.LAUNCHING,
            SuperState.READY,
            SuperState.FINISHED,
        ):
            cmdMsg.drive.speed = 0.0
            cmdMsg.drive.steering_angle = 0.0
        
        elif self.currentState == SuperState.RUNNING:
            cmdMsg.drive.speed = self.vel
            cmdMsg.drive.steering_angle = self.steer
        
        elif self.currentState == SuperState.STOPPING:
            cmdMsg.drive.steering_angle = self.steer
            if self.currentVel > 0.1:
                targetVel = 0.5 * self.currentVel
            else:
                targetVel = 0.0
            cmdMsg.drive.speed = targetVel

        cmdMsg.header.stamp = self.communication.get_clock().now().to_msg()
        return cmdMsg

    # ========================
    # ROS CALLBACKS
    # ========================

    def onCANState(self, data):
        """
        Input  : data (str) — CAN state data from ROS topic
        Output : None
        Logic  : Update internal asState or amiState.
                 Trigger state transitions if conditions are met.
        """
        # Extract fields from the CanState message
        self.asState = data.as_state
        self.amiState = data.ami_state
        
        self.logger.debug(f"[Supervisor] CAN State - AS: {self.asState}, AMI: {self.amiState}")
        

    def onVelocity(self, data):
        """
        Input  : data (float) — velocity value in m/s
        Output : None
        Logic  : Process velocity update.
                 Used for mission monitoring or safety checks.
        """
        self.currentVel = data
        

    def onControl(self, msg):
        """
        Input  : msg (AckermannDriveStamped) — control command
        Output : None
        Logic  : Extract velocity and steering for monitoring.
        """
        self.vel = msg.drive.speed
        self.steer = msg.drive.steering_angle

    # ========================
    # Heartbeat Monitoring
    # ========================  

    def onHeartbeat(self, pkg: str):
        """
        Input  : pkg (str) — package name that sent the heartbeat
        Output : None
        Logic  : Look up module by pkg in moduleManager.
                 Update module.lastHeartbeatTime = time.time().
                 Set module.state = Running.
        """
        current_time = time.time()

        # Update module_last_heartbeat dict (kept for quick lookup)
        self.module_last_heartbeat[pkg] = current_time

        # Update module state in ModuleManager
        module = self.moduleManager.getModule(pkg)

        if module:
            if module.state != ModuleState.Running:
                module.state = ModuleState.Running
                self.logger.info(f"[Supervisor] Module {pkg} is now RUNNING (heartbeat received)")

            # Record heartbeat timestamp on module object as well
            module.lastHeartbeatTime = current_time
        else:
            self.logger.info(f"[Supervisor] Received heartbeat from unknown module: {pkg}")


    def checkHeartbeat(self):
        current_time = time.time()
        modules = self.moduleManager.getModules()

        for pkg, module in modules.items():

            # Skip modules explicitly in Error state
            if module.state == ModuleState.Error:
                continue

            if module.state not in (ModuleState.Running, ModuleState.Starting):
                continue

            timeout = getattr(module, 'heartbeatTimeout', self.heartbeat_timeout)

            # Prefer module_last_heartbeat for authoritative last-seen timestamp,
            # fall back to module.lastHeartbeatTime if missing.
            last_heartbeat = self.module_last_heartbeat.get(pkg, getattr(module, 'lastHeartbeatTime', 0))

            # No heartbeat yet
            if not last_heartbeat:
                if module.state == ModuleState.Starting:
                    started_since = current_time - getattr(module, 'startTime', current_time)
                    startup_timeout = getattr(module, 'startupTimeout', max(2.0 * timeout, 1.0))

                    if started_since > startup_timeout:

                        if current_time - module.lastRestartTime < module.restartCooldown:
                            continue

                        module.state = ModuleState.Unresponsive

                        self.logger.info(
                            f"[Supervisor] Module {pkg} never reported heartbeat after start; restarting"
                        )

                        self.issueCommand(RestartModuleCommand(self.moduleManager, module, self.logger))
                continue

            # Normal timeout case
            time_since_heartbeat = current_time - last_heartbeat

            if time_since_heartbeat > timeout:

                if current_time - module.lastRestartTime < module.restartCooldown:
                    continue

                module.state = ModuleState.Unresponsive

                self.logger.info(
                    f"[Supervisor] Module {pkg} heartbeat timeout "
                    f"({time_since_heartbeat:.1f}s > {timeout}s)"
                )

                self.issueCommand(RestartModuleCommand(self.moduleManager, module, self.logger))
    # ========================
    # MISSION CALLBACKS
    # ========================
    def onMissionFinished(self, result):
        """
        Input  : result — mission result data
        Output : None
        Logic  : Transition state to FINISHED.
        """
        self.isFinished = True
        self.logger.info(f"[Supervisor] Mission finished with result: {result}")


    def onMissionFailed(self, reason: str):
        """
        Input  : reason (str) — why the mission failed
        Output : None
        Logic  : Transition state to STOPPING.
                 Issue EmergencyStopCommand.
                 Log the failure reason.
        """
        self.logger.error(f"[Supervisor] Mission failed: {reason}")
        self.currentState = SuperState.STOPPING
        # EmergencyStopCommand expects (missionManager, moduleManager, logger)
        self.issueCommand(EmergencyStopCommand(self.missionManager, self.moduleManager, self.logger))


def main(args=None):
    """ROS2 entrypoint for starting the supervisor system."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger(__name__).info("[SupervisorMain] Booting supervisor node")
    rclpy.init(args=args)

    communication = None
    try:
        from supervisor.helpers.CommunicationLayer import CommunicationLayer
        from supervisor.helpers.Module.ModuleManager import ModuleManager
        from supervisor.helpers.Missions.MissionManager import MissionManager

        communication = CommunicationLayer.getInstance()
        module_manager = ModuleManager()
        mission_manager = MissionManager.getInstance()
        mission_manager.setModuleManager(module_manager)

        Supervisor(communication, mission_manager, module_manager)
        logging.getLogger(__name__).info("[SupervisorMain] Supervisor + CommunicationLayer running")
        communication.spin()

    finally:
        if communication is not None:
            communication.shutdown()
            communication.destroy_node()
        rclpy.shutdown()