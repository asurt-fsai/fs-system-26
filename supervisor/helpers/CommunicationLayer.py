# communication_layer.py

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from threading import Lock
from std_msgs.msg import String


class CommunicationLayer(Node):

    _instance = None
    _instance_lock = Lock()

    # ==================================================
    # SINGLETON
    # ==================================================
    @classmethod
    def getInstance(cls):
        """
        Ensures only one instance of CommunicationLayer exists.
        Thread-safe singleton creation.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = CommunicationLayer()
        return cls._instance

    # ==================================================
    # CONSTRUCTOR
    # ==================================================
    def __init__(self):
        super().__init__('communication_layer')

        # Shared state
        self.activeMission = None          # Currently running mission object
        self.registeredModules = []        # List of module objects
        self.supervisor = None             # Supervisor reference

        # Lock protecting shared state
        self.state_lock = Lock()

        self.initROS()

    # ==================================================
    # ROS INITIALIZATION
    # ==================================================
    def initROS(self):
        self.setupPublishers()
        self.setupSubscriptions()

    # ==================================================
    # PUBLISHERS
    # ==================================================
    def setupPublishers(self):
        self.drive_pub = self.create_publisher(String, 'drive_command', 10)
        self.can_pub = self.create_publisher(String, 'can_command', 10)

    # ==================================================
    # SUBSCRIPTIONS
    # ==================================================
    def setupSubscriptions(self):

        self.create_subscription(String, 'can_state', self.onCANState, 10)
        self.create_subscription(String, 'velocity', self.onVelocity, 10)
        self.create_subscription(String, 'control', self.onControl, 10)
        self.create_subscription(String, 'heartbeat', self.on_heartbeat, 10)
        self.create_subscription(String, 'cone_detection', self.onConeDetection, 10)
        self.create_subscription(String, 'loop_closure', self.onLoopClosure, 10)
        self.create_subscription(String, 'distance', self.onDistance, 10)

    # ==================================================
    # SPIN
    # ==================================================
    def spin(self):
        executor = MultiThreadedExecutor()
        executor.add_node(self)
        executor.spin()

    # ==================================================
    # REGISTRATION METHODS
    # ==================================================
    def registerSupervisor(self, supervisor):
        with self.state_lock:
            self.supervisor = supervisor

    def registerMission(self, mission):
        with self.state_lock:
            self.activeMission = mission

    def registerModule(self, module):
        with self.state_lock:
            self.registeredModules.append(module)

    # ==================================================
    # CALLBACKS
    # ==================================================
    def onCANState(self, msg):
        with self.state_lock:
            supervisor = self.supervisor
        if supervisor:
            supervisor.onCANState(msg.data)

    def onVelocity(self, msg):
        with self.state_lock:
            supervisor = self.supervisor
        if supervisor:
            supervisor.onVelocity(msg.data)

    def onControl(self, msg):
        with self.state_lock:
            supervisor = self.supervisor
        if supervisor:
            supervisor.issueCommand(msg.data)

    def on_heartbeat(self, msg):
        with self.state_lock:
            modules_copy = list(self.registeredModules)

        for module in modules_copy:
            if module.pkg == msg.data:
                module.on_heartbeat()

    def onConeDetection(self, msg):
        with self.state_lock:
            mission = self.activeMission

        if mission:
            mission.onConeDetected(msg.data)

    def onLoopClosure(self, msg):
        with self.state_lock:
            mission = self.activeMission

        if mission:
            mission.onLoopClosure(msg.data)

    def onDistance(self, msg):
        with self.state_lock:
            mission = self.activeMission

        if mission:
            mission.onDistance(msg.data)

    # ==================================================
    # PUBLISH METHODS
    # ==================================================
    def publishDriveCommand(self, cmd):
        msg = String()
        msg.data = cmd
        self.drive_pub.publish(msg)

    def publishCANCommand(self, state):
        msg = String()
        msg.data = state
        self.can_pub.publish(msg)