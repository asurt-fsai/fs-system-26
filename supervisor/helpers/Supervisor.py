import time
import threading
import logging
from enum import Enum
from supervisor.helpers.Commands import ShutdownModulesCommand,StartMissionCommand,EmergencyStopCommand,RestartModuleCommand
from supervisor.helpers.Module.ModuleState import ModuleState
from eufs_msgs.msg import CanState
from geometry_msgs.msg import TwistWithCovarianceStamped
from ackermann_msgs.msg import AckermannDriveStamped

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

        # Heartbeat tracking
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
                self.issueCommand(StartMissionCommand(self.missionManager, self.amiState)) #amiState is the target mission type, passed to StartMissionCommand

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
                self.issueCommand(ShutdownModulesCommand(self.moduleManager))
                self.logger.info("[Supervisor] Entered FINISHED")

            elif time.time() - self.finished_time > 5:
                self.currentState = SuperState.WAITING
                self.amiState = CanState.AMI_NOT_SELECTED
                self.isFinished = False
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
        from ackermann_msgs.msg import AckermannDriveStamped
        
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
        
        # Update heartbeat timestamp
        self.module_last_heartbeat[pkg] = current_time
        
        # Update module state in ModuleManager
        module = self.moduleManager.getModule(pkg)
        
        if module:
            if module.state != ModuleState.RUNNING:
                module.state = ModuleState.RUNNING
                self.logger.info(f"[Supervisor] Module {pkg} is now RUNNING (heartbeat received)")
            
            module.lastHeartbeatTime = current_time
        else:
            self.logger.warning(f"[Supervisor] Received heartbeat from unknown module: {pkg}")


    def checkHeartbeat(self):
        """
        Input  : None
        Output : None
        Logic  : Iterate all modules in moduleManager.
                 For each module in Running state check if
                 time.time() - lastHeartbeatTime > heartbeatTimeout.
                 If timeout exceeded issue RestartModuleCommand.
        """
        current_time = time.time()
        modules = self.moduleManager.getModules()
        
        for pkg, module in modules.items():
            # Only check modules that should be running
            if module.state != ModuleState.RUNNING:
                continue
            
            # Get last heartbeat time
            last_heartbeat = self.module_last_heartbeat.get(pkg, 0)
            
            # Check timeout
            time_since_heartbeat = current_time - last_heartbeat
            
            if time_since_heartbeat > self.heartbeat_timeout:
                self.logger.warning(
                    f"[Supervisor] Module {pkg} heartbeat timeout "
                    f"({time_since_heartbeat:.1f}s > {self.heartbeat_timeout}s)"
                )
                
                # Issue restart command
                self.issueCommand(RestartModuleCommand(self.moduleManager, module))

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
        self.currentState = SuperState.STOPPING
        self.logger.info(f"Mission finished with result: {result}")


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
        self.issueCommand(EmergencyStopCommand(self.moduleManager,self.missionManager))