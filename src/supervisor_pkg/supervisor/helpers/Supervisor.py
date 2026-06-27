import json
import time
import threading
import logging
from enum import Enum
from supervisor.helpers.CommunicationLayer import CommunicationLayer
import rclpy
from supervisor.helpers.Commands.ShutdownModulesCommand import ShutdownModulesCommand
from supervisor.helpers.Commands.EmergencyStopCommand import EmergencyStopCommand
from supervisor.helpers.Commands.RestartModuleCommand import RestartModuleCommand
from supervisor.helpers.Commands.StartMissionCommand import StartMissionCommand
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.msg import CanState
from supervisor.helpers.Commands.DockerStopCommand import DockerStopCommand
from supervisor.helpers.Commands.DockerLaunchCommand import DockerLaunchCommand
from supervisor.helpers.clients.mission_manager_client import MissionManagerClient
from supervisor.helpers.clients.module_manager_client import ModuleManagerClient
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
        communication:CommunicationLayer,
        mission_manager_client:MissionManagerClient,
        module_manager_client:ModuleManagerClient,
        moduleManager:ModuleManager,
        heartbeat_timeout=5.0,
    ):
        """
        Input  : communication (CommunicationLayer) — event bus
                 mission_manager_client (MissionManagerClient) — mission control publisher
                 module_manager_client (ModuleManagerClient) — module control publisher
                 moduleManager (ModuleManager) — local module state registry
                 heartbeat_timeout (float) — seconds before timeout
        Output : None
        Logic  : Store all references.
                 Initialize currentState = superstate.WAITING.
                 Initialize monitor thread references.
                 Register self with communication layer.
        """
        self.communication = communication
        self.missionManagerClient = mission_manager_client
        self.moduleManagerClient = module_manager_client
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
        self.mission_status = None
        self.useDocker = False

        # Register with managers
        self.communication.registerSupervisor(self)
        self.moduleManager.setSupervisor(self)  # If ModuleManager needs it
        self.logger.info("[Supervisor] Initialized in WAITING state")


    def issueCommand(self, cmd):
        """
        Input  : cmd (Command) — any command implementing execute()
        Output : None
        Logic  : Call cmd.execute().
        """
        try:
            if cmd.__class__.__name__ == "StartMissionCommand":
                if self.asState not in (CanState.AS_OFF, CanState.AS_FINISHED):
                    self.logger.warning(
                        "[Supervisor] StartMissionCommand blocked: AS state not OFF/FINISHED"
                    )
                    return
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

    def transitionState(self):
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
                        self.issueCommand(
                            StartMissionCommand(
                                self.missionManagerClient,
                                mission_type,
                                self.logger,
                            )
                        )
                        self.active_mission = mission_type

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

                if self.useDocker:
                    if (
                        hasattr(self, "missionManagerClient")
                        and self.missionManagerClient is not None
                    ):
                        self.mission_status = MissionStatus.RUNNING
                else:
                    self.mission_status = MissionStatus.RUNNING

                self.currentState = SuperState.RUNNING
                self.logger.info("[Supervisor] State transition to RUNNING")

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

                    self.issueCommand(
                        ShutdownModulesCommand(
                            self.moduleManagerClient,
                            self.logger,
                        )
                    )

                self.logger.info("[Supervisor] Entered FINISHED")

            elif time.time() - self.finished_time > 5:

                self.currentState = SuperState.WAITING
                self.amiState = CanState.AMI_NOT_SELECTED
                self.isFinished = False

                if self.useDocker:
                    self.activeMissionName = None
                else:
                    self.missionManagerClient.stop_mission()
                    self.active_mission = None

                del self.finished_time

                self.logger.info("[Supervisor] Reset to WAITING")    


    def run(self):
        self.logger.info(f"RUN currentState={self.currentState} isFinished={self.isFinished}")
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
        self.issueCommand(StartMissionCommand(self.missionManagerClient, mission_type, self.logger))

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

    # ========================
    # Mission Manager Callbacks
    # ========================

    def onMissionModules(self, payload: str) -> None:
        """
        Input  : payload (str) — JSON string with modules list
        Output : None
        Logic  : Parse and register module list for heartbeat tracking.
        """
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self.logger.error("[Supervisor] Failed to parse mission modules JSON")
            return

        modules = []
        for entry in data.get("modules", []):
            if not isinstance(entry, dict):
                continue
            if "pkg" not in entry or "launch_file" not in entry:
                continue
            module = Module(
                entry["pkg"],
                entry["launch_file"],
                None,
                None,
                entry.get("heartbeat_timeout", 5.0),
                entry.get("startup_timeout"),
                entry.get("heartbeats_topic") or entry.get("heartbeat_topic"),
            )
            module.state = ModuleState.Starting
            module.startTime = time.time()
            modules.append(module)

        self.moduleManager.registerModules(modules)
        self.communication.registerModuleHeartbeats(modules)
        if not modules:
            self.module_last_heartbeat = {}
        self.logger.info(f"[Supervisor] Registered {len(modules)} mission modules")

    def onMissionResult(self, payload: str) -> None:
        """Handle mission result published by mission node."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"status": payload}

        status = str(data.get("status", "")).upper()
        if status == "FINISHED":
            self.onMissionFinished(status)
        elif status == "FAILED":
            reason = data.get("reason", "unknown")
            self.onMissionFailed(str(reason))

    def _modules_ready(self) -> bool:
        modules = self.moduleManager.getModules()
        if not modules:
            return self.active_mission in (
                MissionType.STATIC_A,
                MissionType.STATIC_B,
                MissionType.AUTODEMO,
            )
        for module in modules.values():
            if module.state != ModuleState.Running:
                return False
        return True

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
                        module.lastRestartTime = current_time

                        self.logger.info(
                            f"[Supervisor] Module {pkg} never reported heartbeat after start; restarting"
                        )

                        self.issueCommand(
                            RestartModuleCommand(self.moduleManagerClient, module.pkg, self.logger)
                        )
                continue

            # Normal timeout case
            time_since_heartbeat = current_time - last_heartbeat

            if time_since_heartbeat > timeout:

                if current_time - module.lastRestartTime < module.restartCooldown:
                    continue

                module.state = ModuleState.Unresponsive
                module.lastRestartTime = current_time

                self.logger.info(
                    f"[Supervisor] Module {pkg} heartbeat timeout "
                    f"({time_since_heartbeat:.1f}s > {timeout}s)"
                )

                self.issueCommand(
                    RestartModuleCommand(self.moduleManagerClient, module.pkg, self.logger)
                )
    # ========================
    # MISSION CALLBACKS
    # ========================
    def onMissionFinished(self, result):
        """
        Input  : result — mission result data
        Output : None
        Logic  : Transition state to FINISHED.
        """
        self.logger.info("onMissionFinished")
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
        # EmergencyStopCommand expects (mission_manager_client, module_manager_client, logger)
        self.issueCommand(
            EmergencyStopCommand(self.missionManagerClient, self.moduleManagerClient, self.logger)
        )


def main(args=None):
    
    """ROS2 entrypoint for starting the supervisor system."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger(__name__).info("[SupervisorMain] Booting supervisor node")
    rclpy.init(args=args)

    communication = None
    try:
        from supervisor.helpers.CommunicationLayer import CommunicationLayer
        from supervisor.helpers.Module.ModuleManager import ModuleManager
        from supervisor.helpers.clients.mission_manager_client import MissionManagerClient
        from supervisor.helpers.clients.module_manager_client import ModuleManagerClient

        communication = CommunicationLayer.getInstance()
        module_manager = ModuleManager()
        mission_manager_client = MissionManagerClient(communication)
        module_manager_client = ModuleManagerClient(communication)

        Supervisor(
            communication,
            mission_manager_client,
            module_manager_client,
            module_manager,
        )
        logging.getLogger(__name__).info("[SupervisorMain] Supervisor + CommunicationLayer running")
        communication.spin()

    finally:
        if communication is not None:
            communication.shutdown()
            communication.destroy_node()
        rclpy.shutdown()