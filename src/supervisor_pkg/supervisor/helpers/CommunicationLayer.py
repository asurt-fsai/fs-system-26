"""
CommunicationLayer — Singleton ROS2 Adapter / Event Bus

Role in Architecture
--------------------
This class acts as the central communication hub of the system.
It connects ROS2 topics with the internal system components:

ROS Topics  --->  CommunicationLayer  --->  Supervisor / Mission

The class contains NO business logic.
It only routes events to the correct subsystem.

Architecture Alignment
----------------------
CommunicationLayer --> Supervisor
CommunicationLayer --> MissionFinishing

Threading Model
---------------
1. ROS2 MultiThreadedExecutor threads handle callbacks
2. One background monitor thread prints health logs

"""""

import os
import logging
import threading
from threading import Thread, Event
from typing import Optional

from enum import Enum

import rclpy
import rclpy.node


from supervisor.helpers.Module.ModuleState import ModuleState
from eufs_msgs.msg import CanState
from asurt_msgs.msg import NodeStatus
from geometry_msgs.msg import TwistWithCovarianceStamped
from std_msgs.msg import Bool, Float64, Int16, String
from std_srvs.srv import Trigger

from rclpy.executors import MultiThreadedExecutor

from ackermann_msgs.msg import AckermannDriveStamped

from supervisor.helpers.Commands.StartMissionCommand import StartMissionCommand
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.Missions.MissionStatus import MissionStatus






class CommunicationLayer(rclpy.node.Node):

    """
    Singleton EventBus that connects ROS2 topics with internal system components.
    """

    # ---------------------------------------------------------
    # Singleton Storage
    # ---------------------------------------------------------

    _instance = None
    _initialised = False

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    MONITOR_INTERVAL = 5.0
    LOG_DIR = "logs"
    LOG_FILE = "communication_layer.log"

    # ---------------------------------------------------------
    # Singleton Constructor
    # ---------------------------------------------------------

    def __new__(cls, *args, **kwargs):

        """
        Ensures only ONE instance of CommunicationLayer exists.

        Output
        ------
        CommunicationLayer instance
        """

        if cls._instance is None:
            cls._initialised = False
            cls._instance = super().__new__(cls)

        return cls._instance

    @classmethod
    def getInstance(cls):

        """
        Public access to the singleton instance.

        Output
        ------
        CommunicationLayer instance
        """

        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(self):

        """
        Initializes the ROS2 node and internal references.

        Input
        -----
        None

        Output
        ------
        CommunicationLayer object

        Logging
        -------
        Logs initialization event.
        """

        if CommunicationLayer._initialised:
            return

        CommunicationLayer._initialised = True

        super().__init__("communication_layer")

        # Registered system components
        self._supervisor = None
        self._activeMission = None
        self._last_mission_name = None

        # Thread control
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None

        # Setup subsystems
        self._setup_logger()
        self._init_ros()
        self._start_monitor()

        self.logger.debug("CommunicationLayer initialised")

    # ---------------------------------------------------------
    # Logger Setup
    # ---------------------------------------------------------

    def _setup_logger(self):

        """
        Creates the system logging infrastructure.

        Input
        -----
        None

        Output
        ------
        File logger writing to:
        logs/communication_layer.log

        Logging
        -------
        All events in this layer are written to the log file.
        """

        os.makedirs(self.LOG_DIR, exist_ok=True)

        self.logger = logging.getLogger("communication_layer")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:

            handler = logging.FileHandler(
                os.path.join(self.LOG_DIR, self.LOG_FILE)
            )

            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s communication_layer %(message)s"
                )
            )

            self.logger.addHandler(handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
            )
            self.logger.addHandler(stream_handler)

    # ---------------------------------------------------------
    # Background Monitor Thread
    # ---------------------------------------------------------

    def _start_monitor(self):

        """
        Starts the background monitor thread.

        Purpose
        -------
        Periodically prints "CommunicationLayer alive"
        to verify the system is still running.

        Thread
        ------
        daemon thread named 'cl-monitor'
        """

        if self._monitor_thread is not None:
            return

        t = Thread(
            target=self._background_monitor,
            name="cl-monitor",
            daemon=True
        )

        self._monitor_thread = t
        t.start()

        self.logger.debug(f"[thread={t.name}] Background monitor started")

    def _background_monitor(self):

        """
        Monitor loop executed in a background thread.

        Behavior
        --------
        Every MONITOR_INTERVAL seconds the system logs
        that the communication layer is alive.

        Logging
        -------
        DEBUG: "CommunicationLayer alive"
        """

        while not self._stop_event.is_set():

            self.logger.debug(
                f"[thread={threading.current_thread().name}] CommunicationLayer alive"
            )

            self._stop_event.wait(timeout=self.MONITOR_INTERVAL)

    # ---------------------------------------------------------
    # ROS Initialization
    # ---------------------------------------------------------

    def _init_ros(self):

        """
        Initializes ROS publishers , subscribers and timers.

        Input
        -----
        None

        Output
        ------
        Active ROS2 topics.

        """

        self._setup_publishers()
        self._setup_subscriptions()
        self._setup_timers()
        self._ebs_client = self.create_client(Trigger, "/ros_can/ebs")
       
    # ---------------------------------------------------------
    # Publishers
    # ---------------------------------------------------------

    def _setup_publishers(self):

        """
        Creates publishers used to send commands.

        Topics
        ------
        /drive_command
        /can_command
        /driving_flag
        /mission_flag
        """
        #  Ackermann drive command
        self._cmd_pub = self.create_publisher( AckermannDriveStamped, "/ros_can/cmd", 10)

        # Driving flag (enables autonomous driving)
        self._driving_flag_pub = self.create_publisher(Bool,"/ros_can/driving_flag",10)
        # Mission finished flag
        self._mission_flag_pub = self.create_publisher(Bool,"/ros_can/mission_flag",10)
        self._mission_state_pub = self.create_publisher(String, "/static_mission/state", 10)

    # ---------------------------------------------------------
    # Subscriptions
    # ---------------------------------------------------------

    def _setup_subscriptions(self):

        """
        Creates subscriptions for system topics.

        Topics handled
        --------------
        CAN state
        velocity
        control
        heartbeat
        cone detection
        loop closure
        distance
        loop closure count
        """

        # CAN state — uses CanState message type
        self.create_subscription(CanState,'/ros_can/state',self.onCANState,10)

        self.create_subscription(NodeStatus, "/module_heartbeat", self.onHeartbeat, 10)

        self.create_subscription(TwistWithCovarianceStamped,'/current_velocity', self.onVelocity,10)
        
        self.create_subscription(AckermannDriveStamped,'/control', self.onControl,10)
        # Bool topics
        bool_topics = [
            ("/perception/cone_detection", self.onConeDetection),
            ("/slam/loop_closure",         self.onLoopClosure),
        ]
        for topic, callback in bool_topics:
            self.create_subscription(Bool, topic, callback, 10)

        # Float64 topics
        self.create_subscription(Float64, "/slam/distance", self.onDistance, 10)
           
        self.create_subscription(Int16, "/slam/loop_closure_count",self.onLoopClosureCount,10)

        # GUI coordination topics
        self.create_subscription(String, "/missionName", self.onMissionName, 10)
        self.create_subscription(Bool, "/supervisor/driving_flag", self.onSupervisorDrivingFlag, 10)

    # ---------------------------------------------------------
    # Timers
    # ---------------------------------------------------------
    def _setup_timers(self):
        """
        Creates periodic timers for system loops.
        """
        loop_hz = 2.0
        try:
            loop_hz = float(os.getenv("SUPERVISOR_LOOP_HZ", "2"))
        except ValueError:
            loop_hz = 2.0
        loop_hz = max(0.1, loop_hz)
        loop_period = 1.0 / loop_hz
        self.logger.info(f"[Supervisor] Loop period set to {loop_period:.2f}s ({loop_hz:.2f} Hz)")

        # Supervisor main loop (like old run())
        self.create_timer(loop_period, self._supervisor_loop)

        #timer for heartbeat 
        self.create_timer(1.0, self._heartbeat_monitor)  # 1 Hz



    def _supervisor_loop(self):
        supervisor = self._supervisor
        if not supervisor:
            return
        try:
            supervisor.run()
            active = self._activeMission
            if active and hasattr(active, "tick"):
                active.tick()
        except Exception as e:
            self.logger.error(f"[Supervisor Loop Error] {e}", exc_info=True)

    def _heartbeat_monitor(self):
        supervisor = self._supervisor
        if not supervisor:
            return
        try:
            supervisor.checkHeartbeat()
        except Exception as e:
            self.logger.error(f"[Heartbeat Error] {e}", exc_info=True)

    # ---------------------------------------------------------
    # ROS Executor
    # ---------------------------------------------------------

    def spin(self):

        """
        Starts the ROS2 executor.

        Threading
        ---------
        MultiThreadedExecutor allows multiple callbacks
        to run concurrently.

        Output
        ------
        Infinite ROS2 event loop.
        """

        executor = MultiThreadedExecutor()
        executor.add_node(self)
        executor.spin()

    # ---------------------------------------------------------
    # Registration API
    # ---------------------------------------------------------

    def registerSupervisor(self, supervisor):

        """
        Registers the system Supervisor.

        Input
        -----
        supervisor : Supervisor

        Output
        ------
        Stores reference for event routing.

        Logging
        -------
        INFO entry when supervisor is registered.
        """

        self._supervisor = supervisor

        self.logger.info(
            f"[register] Supervisor registered"
        )

    def registerMission(self, mission):

        """
        Registers the active mission.

        Input
        -----
        mission : MissionFinishing

        Output
        ------
        Stores mission strategy instance.
        """

        self._activeMission = mission
        if mission is None:
            self.logger.info("[register] Mission cleared")
            return

        self.logger.info(
            f"[register] Mission registered: {type(mission).__name__}"
        )

    # ---------------------------------------------------------
    # Supervisor Callbacks
    # ---------------------------------------------------------

    def onCANState(self, msg):

        """
        Handles CAN state messages.

        Input
        -----
        msg : ROS message containing CAN state

        Output
        ------
        Forwarded to Supervisor.

        Logging
        -------
        INFO log of received state.
        """

        self._log_topic("/ros_can/state", f"as_state={msg.as_state}, ami_state={msg.ami_state}")
    
        if self._supervisor:
            self._supervisor.onCANState(msg)  # Pass entire message object

    def onVelocity(self, msg):

        """
        Handles vehicle velocity updates.

        Input
        -----
        msg :  msg (TwistWithCovarianceStamped) — velocity message

        Output
        ------
        Forwarded to Supervisor.
        """

        # Extract velocity from Twist message
        velocity = msg.twist.twist.linear.x
        
        self._log_topic("/current_velocity", f"{velocity:.2f} m/s")

        if self._supervisor:
            self._supervisor.onVelocity(velocity)  # Pass the float value


    def onControl(self, msg):

        """
        Handles control system messages.

        Input
        -----
        msg : msg (AckermannDriveStamped) — control command

        Output
        ------
        Routed to Supervisor.
        """

        vel = msg.drive.speed
        steer = msg.drive.steering_angle
            
        self._log_topic("/control", f"speed={vel:.2f}, steer={steer:.2f}")

        if self._supervisor and hasattr(self._supervisor, "onControl"):
            self._supervisor.onControl(msg)  # Pass entire message

    def onMissionName(self, msg: String):
        self._last_mission_name = msg.data

    def _mission_type_from_name(self, name: str):
        if not name:
            return None
        normalized = name.strip().lower()
        mapping = {
            "static a": MissionType.STATIC_A,
            "statica": MissionType.STATIC_A,
            "static b": MissionType.STATIC_B,
            "staticb": MissionType.STATIC_B,
            "autonomus demo": MissionType.AUTODEMO,
            "autonomous demo": MissionType.AUTODEMO,
            "autodemo": MissionType.AUTODEMO,
        }
        return mapping.get(normalized)

    def onSupervisorDrivingFlag(self, msg: Bool):
        self._log_topic("/supervisor/driving_flag", msg.data)
        if not msg.data:
            return

        mission_type = self._mission_type_from_name(self._last_mission_name)
        if mission_type is None:
            self.logger.warning("[Supervisor] driving_flag received but no static mission selected")
            return

        if not self._supervisor:
            self.logger.warning("[Supervisor] driving_flag received but supervisor not registered")
            return

        active = self._supervisor.missionManager.activeMission
        if active and getattr(active, "missionStatus", None) in (MissionStatus.IDLE, MissionStatus.RUNNING):
            self.logger.warning("[Supervisor] driving_flag ignored: mission already active")
            return

        self.logger.info(f"[Supervisor] driving_flag -> starting {mission_type.name}")
        self._supervisor.issueCommand(
            StartMissionCommand(self._supervisor.missionManager, mission_type, self.logger)
        )


    def onHeartbeat(self, msg):

        """
        Handles module heartbeat messages.

        Input
        -----
        msg (NodeStatus) — heartbeat status message

        Output
        ------
        Forwarded to Supervisor.

        Supervisor will update ModuleManager heartbeat state.
        """
        module_name = msg.message
        status = msg.status

        self._log_topic("/module_heartbeat", f"{module_name} - {status}")

        if self._supervisor:
            self._supervisor.onHeartbeat(module_name)

    # ---------------------------------------------------------
    # Mission Callbacks
    # ---------------------------------------------------------

    def onConeDetection(self, msg):

        """
        Routes cone detection events to the active mission.

        Input
        -----
        msg.data : cone detection info
        """

        self._log_topic("/perception/cone_detection", msg.data)

        if self._activeMission:
            self._activeMission.onConeDetected(msg.data)

    def onLoopClosure(self, msg):

        """
        Routes loop closure events to mission logic.
        """

        self._log_topic("/slam/loop_closure", msg.data)

        if self._activeMission:
            self._activeMission.onLoopClosure(msg.data)

    def onLoopClosureCount(self, msg):
        """
        Handles loop closure count for Trackdrive mission.
        
        Input : msg (Int16) — loop closure count
        """
        self._log_topic("/slam/loop_closure_count", msg.data)
        
        if self._activeMission and hasattr(self._activeMission, 'onLoopClosureCount'):
            self._activeMission.onLoopClosureCount(msg.data)

    def onDistance(self, msg):

        """
        Routes distance updates to the mission strategy.

        Input
        -----
        msg.data : current vehicle distance

        Output
        ------
        Mission checks if finishing condition is met.
        """

        self._log_topic("/slam/distance", msg.data)

        if self._activeMission:
            self._activeMission.onDistance(msg.data)

    # ---------------------------------------------------------
    # Publish API
    # ---------------------------------------------------------

    def publishDriveCommand(self, cmd_msg):

        """
        Publishes Ackermann drive commands.

        Input
        -----
        cmd : cmd_msg (AckermannDriveStamped) — drive command

        Output
        ------
        ROS message sent to /drive_command
        """
        self._cmd_pub.publish(cmd_msg)

        self._log_publish("drive_command", f"speed={cmd_msg.drive.speed:.2f}, steer={cmd_msg.drive.steering_angle:.2f}")

    def publishDrivingFlag(self, flag: bool):
        """
        Publishes driving flag.
        
        Input : flag (bool) — True to enable autonomous driving
        """
        msg = Bool()
        msg.data = flag
        self._driving_flag_pub.publish(msg)
        self._log_publish("driving_flag", flag) 

    def publishMissionFlag(self, flag: bool):
        """
        Publishes mission finished flag.
        
        Input : flag (bool) — True when mission is finished
        """
        msg = Bool()
        msg.data = flag
        self._mission_flag_pub.publish(msg)
        self._log_publish("mission_flag", flag)  

    def publishMissionState(self, state: str):
        msg = String()
        msg.data = state
        self._mission_state_pub.publish(msg)
        self._log_publish("static_mission/state", state)
    
    def triggerEBS(self): # for static B mission
        if not self._ebs_client.wait_for_service(timeout_sec=1.0):
            self.logger.error("EBS service not available")
            return

        req = Trigger.Request()
        self._ebs_client.call_async(req)
    # ---------------------------------------------------------
    # Logging Helpers
    # ---------------------------------------------------------

    def _log_topic(self, topic, data):

        """
        Logs received ROS topic messages.

        Format
        ------
        [thread=X] [topic=Y] data=Z
        """

        thread = threading.current_thread().name

        self.logger.info(
            f"[thread={thread}] [topic={topic}] data={data}"
        )

    def _log_publish(self, topic, data):

        """
        Logs outgoing ROS messages.
        """

        thread = threading.current_thread().name

        self.logger.info(
            f"[thread={thread}] [publish={topic}] data={data}"
        )

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def shutdown(self):

        """
        Gracefully stops background threads.

        Input
        -----
        None

        Output
        ------
        Stops monitor thread and closes node.
        """

        self._stop_event.set()

        if self._monitor_thread:
            self._monitor_thread.join(timeout=self.MONITOR_INTERVAL)

        self.logger.debug("CommunicationLayer shutdown complete")