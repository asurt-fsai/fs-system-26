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

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String


class CommunicationLayer(Node):

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
        self.logger.setLevel(logging.DEBUG)

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
        Initializes ROS publishers and subscribers.

        Input
        -----
        None

        Output
        ------
        Active ROS2 topics.

        """

        self._setup_publishers()
        self._setup_subscriptions()

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
        """

        self._drive_pub = self.create_publisher(
            String, "drive_command", 10
        )

        self._can_pub = self.create_publisher(
            String, "can_command", 10
        )

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
        """

        topics = [

            ("can_state", self.onCANState),
            ("velocity", self.onVelocity),
            ("control", self.onControl),
            ("heartbeat", self.onHeartbeat),
            ("cone_detection", self.onConeDetection),
            ("loop_closure", self.onLoopClosure),
            ("distance", self.onDistance),
        ]

        for topic, callback in topics:

            self.create_subscription(
                String,
                topic,
                callback,
                10
            )

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

        self._log_topic("can_state", msg.data)

        if self._supervisor:
            self._supervisor.onCANState(msg.data)

    def onVelocity(self, msg):

        """
        Handles vehicle velocity updates.

        Input
        -----
        msg : velocity value

        Output
        ------
        Forwarded to Supervisor.
        """

        self._log_topic("velocity", msg.data)

        if self._supervisor:
            self._supervisor.onVelocity(msg.data)

    def onControl(self, msg):

        """
        Handles control system messages.

        Input
        -----
        msg : control data

        Output
        ------
        Routed to Supervisor.
        """

        self._log_topic("control", msg.data)

        if self._supervisor and hasattr(self._supervisor, "onControl"):
            self._supervisor.onControl(msg.data)

    def onHeartbeat(self, msg):

        """
        Handles module heartbeat messages.

        Input
        -----
        msg.data : module name

        Output
        ------
        Forwarded to Supervisor.

        Supervisor will update ModuleManager heartbeat state.
        """

        module_name = msg.data

        self._log_topic("heartbeat", module_name)

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

        self._log_topic("cone_detection", msg.data)

        if self._activeMission:
            self._activeMission.onConeDetected(msg.data)

    def onLoopClosure(self, msg):

        """
        Routes loop closure events to mission logic.
        """

        self._log_topic("loop_closure", msg.data)

        if self._activeMission:
            self._activeMission.onLoopClosure(msg.data)

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

        self._log_topic("distance", msg.data)

        if self._activeMission:
            self._activeMission.onDistance(msg.data)

    # ---------------------------------------------------------
    # Publish API
    # ---------------------------------------------------------

    def publishDriveCommand(self, cmd):

        """
        Publishes drive commands.

        Input
        -----
        cmd : string command

        Output
        ------
        ROS message sent to /drive_command
        """

        msg = String()
        msg.data = cmd

        self._drive_pub.publish(msg)

        self._log_publish("drive_command", cmd)

    def publishCANCommand(self, state):

        """
        Publishes CAN commands.

        Input
        -----
        state : CAN state command
        """

        msg = String()
        msg.data = state

        self._can_pub.publish(msg)

        self._log_publish("can_command", state)

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
