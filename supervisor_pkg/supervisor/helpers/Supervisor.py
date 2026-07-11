import time
import logging
from enum import Enum
import rclpy
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.Missions.MissionManager import MissionManager
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.msg import CanState
from supervisor.helpers.Commands import DockerLaunchCommand, DockerStopCommand
from supervisor.helpers.Commands.StartMissionCommand import StartMissionCommand
from supervisor.helpers.Commands.StopMissionCommand import StopMissionCommand
from supervisor.helpers.Commands.RestartModuleCommand import RestartModuleCommand
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Module.ModuleManager import ModuleManager
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
    - Mission lifecycle coordination via MissionManagerNode
    - Module health monitoring via ModuleManagerNode
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

    def __init__(
        self,
        communication: CommunicationLayer,
        mission_manager: MissionManager,
        moduleManager: ModuleManager,
        heartbeat_timeout=5.0,
    ):
        """
        Input  : communication (CommunicationLayer) — event bus
                 mission_manager (MissionManager) — inline mission lifecycle manager
                 moduleManager (ModuleManager) — local module state registry
                 heartbeat_timeout (float) — seconds before timeout
        Output : None
        Logic  : Store all references.
                 Initialize currentState = superstate.WAITING.
                 Register self with communication layer.
        """
        self.communication = communication
        self.missionManager = mission_manager
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

        # Mission tracking
        self.mission_ready = False
        self.active_mission = None
        self._last_mission_name = None

        # Docker launch
        self.useDocker = False  # Set to True if using Docker for module launches
        
        # Register with managers
        self.communication.registerSupervisor(self)
        self.moduleManager.setSupervisor(self)
        self.missionManager.setModuleManager(self.moduleManager)
        self.missionManager.setSupervisor(self)
        self.logger.info(
            "[Supervisor] Initialized: currentState=%s asState=%s amiState=%s",
            self.currentState.name,
            self.asState,
            self.amiState,
        )


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
    def _mission_type_from_ami(self, ami_state: int):
        mapping = {
            11: MissionType.ACCELERATION,
            12: MissionType.SKIDPAD,
            13: MissionType.AUTOCROSS,
            14: MissionType.TRACKDRIVE,
            15: MissionType.AUTODEMO,
            18: MissionType.STATIC_A,
            19: MissionType.STATIC_B,
        }
        return mapping.get(ami_state)

    def _log_state_transition(self, old_state, new_state, reason=None):
        self.logger.info(
            "[Supervisor] STATE transition: %s -> %s | as_state=%s ami_state=%s reason=%s",
            old_state.name if old_state is not None else None,
            new_state.name if new_state is not None else None,
            self.asState,
            self.amiState,
            reason,
        )

    def transitionState(self):
        self.logger.info(f"[FLOW] transitionState entered: currentState={self.currentState.name} asState={self.asState} amiState={self.amiState}")
        """
        Input  : None
        Output : None

        Logic:
            - Validate legal state transitions.
            - Update currentState.
            - Log every transition.
            - Keep FINISHED state for 5 seconds before resetting to WAITING.
        """

        if self.currentState == SuperState.WAITING:
            if self.amiState != CanState.AMI_NOT_SELECTED:

                self.currentState = SuperState.LAUNCHING
                self.logger.info(f"transitionState state={self.currentState} finished={self.isFinished}")
                self.logger.info("[Supervisor] State transition to LAUNCHING")

                if self.useDocker:
                    cmd = DockerLaunchCommand(self.amiState)

                    if self.issueCommand(cmd) and cmd.getMissionName():
                        self.activeMissionName = cmd.getMissionName()
                    else:
                        self.logger.error(
                            "[Supervisor] Failed to launch mission with Docker"
                        )
                        self.currentState = SuperState.WAITING
                        self.logger.info(
                            "[Supervisor] Reverting to WAITING state"
                        )

                else:
                    mission_type = self._mission_type_from_ami(self.amiState)

                    if mission_type is None:
                        self.logger.warning(
                            f"[Supervisor] Unknown AMI state for mission start: {self.amiState}"
                        )
                    else:
                        try:
                            self.issueCommand(StartMissionCommand(self.missionManager, mission_type))
                            self.active_mission = mission_type
                            self.logger.info(f"[Supervisor] Mission created and started: {mission_type.name}")
                        except Exception as e:
                            self.logger.error(f"[Supervisor] Failed to start mission: {e}", exc_info=True)
                            self.currentState = SuperState.WAITING

        elif self.currentState == SuperState.LAUNCHING:

            self.isFinished = False

            if self.useDocker:
                self.currentState = SuperState.READY
                self.logger.info("[Supervisor] (Docker) Transition to READY")

            else:
                if self._modules_ready():
                    self.currentState = SuperState.READY
                    self.logger.info("[Supervisor] State transition to READY")

        elif self.currentState == SuperState.READY:
            self.logger.info(f"transitionState state={self.currentState} finished={self.isFinished}")

            if self.asState == 2:  # Vehicle ready to run

                self.currentState = SuperState.RUNNING
                self.logger.info("[Supervisor] State transition to RUNNING")

                # Tell the inline mission object it may now execute
                active = self.missionManager.getActiveMission()
                if active is not None:
                    active.missionStatus = MissionStatus.RUNNING
                    self.logger.info("[Supervisor] Mission missionStatus set to RUNNING")

        elif self.currentState == SuperState.RUNNING:
            self.logger.info(f"transitionState state={self.currentState} finished={self.isFinished}")

            if self.isFinished:
                self.currentState = SuperState.STOPPING
                self.logger.info("[Supervisor] State transition to STOPPING")

        elif self.currentState == SuperState.STOPPING:
            self.logger.info(f"transitionState state={self.currentState} finished={self.isFinished}")

            if self.currentVel < self.maxStopVelTh:
                self.currentState = SuperState.FINISHED
                self.logger.info("[Supervisor] State transition to FINISHED")

        # Keep FINISHED state for 5 seconds so it is published correctly
        elif self.currentState == SuperState.FINISHED:
            self.logger.info(f"transitionState state={self.currentState} finished={self.isFinished}")

            if not hasattr(self, "finished_time"):

                self.finished_time = time.time()

                if self.useDocker:

                    success = self.issueCommand(
                        DockerStopCommand(self.activeMissionName)
                    )

                    if not success:
                        self.logger.error(
                            "[Supervisor] Failed to stop mission with Docker"
                        )

                else:
                    self.issueCommand(StopMissionCommand(self.missionManager))

                self.logger.info("[Supervisor] Entered FINISHED")

            elif time.time() - self.finished_time > 5:

                self.currentState = SuperState.WAITING
                self.amiState = CanState.AMI_NOT_SELECTED
                self.isFinished = False

                if self.useDocker:
                    self.activeMissionName = None
                else:
                    self.active_mission = None

                del self.finished_time

                self.logger.info("[Supervisor] Reset to WAITING")


    def run(self):
        self.transitionState()
        self.publishRosCanMessages()

    #===============================
    # publishing commands to the car
    #================================
    def publishRosCanMessages(self):
        self.logger.info(f"[FLOW] publishRosCanMessages entered: currentState={self.currentState.name}")
        """
        Publishes control flags and commands based on current state.
        Called periodically or after state transitions.
        """
        driving_flag = False
        mission_flag = False

        if self.currentState in (SuperState.WAITING, SuperState.LAUNCHING):
            mission_flag = False
            driving_flag = False

        elif self.currentState == SuperState.READY:
            # AI modules ready — publish Go signal so VCU transitions AS_READY → AS_DRIVING.
            # ros_can translates this into MISSION_RUNNING on the CAN bus; the VCU acts on that.
            mission_flag = False
            driving_flag = True

        elif self.currentState in (SuperState.RUNNING, SuperState.STOPPING):
            mission_flag = False
            driving_flag = True

        elif self.currentState == SuperState.FINISHED:
            mission_flag = True
            driving_flag = False

        self.communication.publishMissionFlag(mission_flag)
        self.communication.publishDrivingFlag(driving_flag)
        self.logger.info(
            "[Supervisor] publish flags: driving_flag=%s mission_flag=%s currentState=%s as_state=%s ami_state=%s",
            driving_flag,
            mission_flag,
            self.currentState.name,
            self.asState,
            self.amiState,
        )

        # Publish drive command (None means static mission owns /cmd — skip)
        cmd_msg = self.getCmdMessage()
        if cmd_msg is not None:
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
            if self.active_mission in (
                MissionType.STATIC_A,
                MissionType.STATIC_B,
                MissionType.AUTODEMO,
            ):
                # Static/AutoDemo mission tick() publishes /cmd directly — supervisor must not interfere.
                return None
            # Dynamic mission: relay /ackr planning commands to /cmd
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
        self.logger.info(f"[FLOW] Supervisor.onCANState entered: as_state={data.as_state} ami_state={data.ami_state}")
        """
        Input  : data (str) — CAN state data from ROS topic
        Output : None
        Logic  : Update internal asState or amiState.
                 Trigger state transitions if conditions are met.
        """
        # Extract fields from the CanState message
        prev_as = self.asState
        prev_ami = self.amiState
        self.asState = data.as_state
        self.amiState = data.ami_state

        if data.as_state == 3 and self.currentState in (
            SuperState.READY, SuperState.RUNNING
        ):
            self.onEmergencyStop("AS_EBS")

        if prev_as != self.asState or prev_ami != self.amiState:
            self.logger.info(
                "[Supervisor] CAN_STATE change: as=%s -> %s | ami=%s -> %s",
                prev_as,
                self.asState,
                prev_ami,
                self.amiState,
            )
        else:
            self.logger.debug(
                "[Supervisor] CAN State unchanged - AS: %s, AMI: %s",
                self.asState,
                self.amiState,
            )

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
    # GUI / External Callbacks
    # ========================

    def onMissionName(self, name: str) -> None:
        self._last_mission_name = name

    def onSupervisorDrivingFlag(self, flag: bool) -> None:
        if not flag:
            return
        if self.active_mission:
            self.logger.warning("[Supervisor] driving_flag ignored: mission already active")
            return
        mission_type = self._mission_type_from_name(self._last_mission_name)
        if mission_type is None:
            self.logger.warning(
                f"[Supervisor] driving_flag received but no known mission name: {getattr(self, '_last_mission_name', None)}"
            )
            return
        self.logger.info(f"[Supervisor] driving_flag -> starting {mission_type.name}")
        try:
            self.issueCommand(StartMissionCommand(self.missionManager, mission_type))
            self.active_mission = mission_type
        except Exception as e:
            self.logger.error(f"[Supervisor] Failed to start mission from driving_flag: {e}", exc_info=True)

    def _mission_type_from_name(self, name: str):
        if not name:
            return None
        mapping = {
            "static a":       MissionType.STATIC_A,
            "statica":        MissionType.STATIC_A,
            "static b":       MissionType.STATIC_B,
            "staticb":        MissionType.STATIC_B,
            "autonomus demo": MissionType.AUTODEMO,
            "autonomous demo":MissionType.AUTODEMO,
            "autodemo":       MissionType.AUTODEMO,
        }
        return mapping.get(name.strip().lower())

    def _modules_ready(self) -> bool:
        if self.active_mission in (
            MissionType.STATIC_A,
            MissionType.STATIC_B,
            MissionType.AUTODEMO,
        ):
            return True
        modules = self.moduleManager.getModules()
        if not modules:
            return True
        for module in modules.values():
            if module.state != ModuleState.Running:
                return False
        return True

    # ========================
    # Heartbeat Monitoring
    # ========================  

    def onHeartbeat(self, pkg: str, status: int = 2):
        """
        Input  : pkg (str) — package name that sent the heartbeat
                 status (int) — NodeStatus.status value (2=RUNNING, 3=ERROR, etc.)
        Output : None
        Logic  : Look up module by pkg in moduleManager.
                 If status indicates error, mark module Error and skip timestamp update
                 so checkHeartbeat triggers a restart after timeout.
                 Otherwise update lastHeartbeatTime and set state = Running.
        """
        current_time = time.time()
        module = self.moduleManager.getModule(pkg)

        if not module:
            self.logger.info(f"[Supervisor] Received heartbeat from unknown module: {pkg}")
            return

        if status == 3:  # ERROR
            self.logger.warning(f"[Supervisor] Module {pkg} reported ERROR status")
            module.state = ModuleState.Error
            return

        # Healthy heartbeat — update timestamp and mark Running
        self.module_last_heartbeat[pkg] = current_time
        module.lastHeartbeatTime = current_time
        if module.state != ModuleState.Running:
            module.state = ModuleState.Running
            self.logger.info(f"[Supervisor] Module {pkg} is now RUNNING (heartbeat received)")


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

                        module.state = ModuleState.Starting
                        module.startTime = current_time
                        module.lastRestartTime = current_time
                        self.module_last_heartbeat.pop(pkg, None)

                        self.logger.info(
                            f"[Supervisor] Module {pkg} never reported heartbeat after start; restarting"
                        )

                        self.issueCommand(RestartModuleCommand(module))
                continue

            # Normal timeout case
            time_since_heartbeat = current_time - last_heartbeat

            if time_since_heartbeat > timeout:

                if current_time - module.lastRestartTime < module.restartCooldown:
                    continue

                module.state = ModuleState.Starting
                module.startTime = current_time
                module.lastRestartTime = current_time
                self.module_last_heartbeat.pop(pkg, None)

                self.logger.info(
                    f"[Supervisor] Module {pkg} heartbeat timeout "
                    f"({time_since_heartbeat:.1f}s > {timeout}s); restarting"
                )

                self.issueCommand(RestartModuleCommand(module))
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
        self.logger.error(f"[Supervisor] Mission failed: {reason}")
        self.currentState = SuperState.STOPPING
        self.issueCommand(StopMissionCommand(self.missionManager))

    def onEmergencyStop(self, source: str = "unknown"):
        self.logger.warning(f"[Supervisor] Emergency stop triggered by {source}")
        self.asState = CanState.AS_EMERGENCY_BRAKE
        self.currentState = SuperState.STOPPING
        self.issueCommand(StopMissionCommand(self.missionManager))


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
        mission_manager = MissionManager()

        Supervisor(
            communication,
            mission_manager,
            module_manager,
        )
        logging.getLogger(__name__).info("[SupervisorMain] Supervisor + CommunicationLayer running")
        communication.spin()

    finally:
        if communication is not None:
            communication.shutdown()
            communication.destroy_node()
        rclpy.shutdown()