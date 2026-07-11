"""
Supervisor main module
"""
from typing import Optional
from enum import Enum
import time
import rclpy
from rclpy.node import Node
import rclpy.time
from std_msgs.msg import Bool, Int16
from eufs_msgs.msg import CanState
from geometry_msgs.msg import TwistWithCovarianceStamped
from ackermann_msgs.msg import AckermannDriveStamped
from supervisor.helpers.missionLauncher import MissionLauncher  # type: ignore
from supervisor.helpers.visualizer import Visualizer  # type: ignore
from asurt_msgs.msg import NodeStatus  # Ensure correct message import




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


class Supervisor(Node):  # pylint: disable=too-many-instance-attributes
    """
    This class is the supervisor's main class
    """

    def __init__(
        self,
        rosCanCmdTopic: str,
        drivingFlagTopic: str,
        missionFlagTopic: str,
        loopClosureCountTopic: str,
        add_node_callback,
        markersTopic: Optional[str] = None,
        btnTopic: Optional[str] = None
    ) -> None:
        super().__init__("Supervisor")
        self.asState = CanState.AS_OFF
        self.amiState = CanState.AMI_NOT_SELECTED
        self.superState = SuperState.WAITING
        self.maxStopVelTh = 0.1
        self.currentVel = 0.0
        self.vel = 0.0
        self.steer = 0.0
        self.shutdown_done = False #to avoid running repeatedly

        self.loopClosureCountTopic = loopClosureCountTopic
        self.add_node_callback = add_node_callback
        self.drivingFlagPub = self.create_publisher(Bool, drivingFlagTopic, 10)
        self.missionFlagPub = self.create_publisher(Bool, missionFlagTopic, 10)
        self.cmd = self.create_publisher(AckermannDriveStamped, rosCanCmdTopic, 10)
        self.heartbeatSub = self.create_subscription(NodeStatus, "/module_heartbeat", self.heartbeatCallback, 10)
        self.isFinishedSub = self.create_subscription(Bool, "/finisher/is_finished", self.isFinishedCallback, 10)

        self.launcher = MissionLauncher(self.add_node_callback)
        self.add_node_callback(self.launcher)

    
        
    
    def heartbeatCallback(self, msg: NodeStatus) -> None:
        """
        Callback to receive heartbeat messages from modules.
        """
        self.get_logger().info(f"Received Heartbeat from {msg.header.frame_id}, Status: {msg.status}")
    
    
    def run(self) -> None:
        """
        Do the state machine transitions and actions
        """

        # # Update launcher
        # if self.superState != SuperState.WAITING:
        #     self.launcher.update()

        # Do transitions
        if self.superState == SuperState.WAITING:
            if self.amiState != CanState.AMI_NOT_SELECTED:
                self.shutdown_done = False
                self.superState = SuperState.LAUNCHING
                self.launcher.launch(self.amiState)
                
        elif self.superState == SuperState.LAUNCHING:
            self.isFinished = False
            self.get_logger().info(f"Launcher ready a33333: {self.launcher.isReady()}")
            if self.launcher.isReady():
                self.superState = SuperState.READY


        elif self.superState == SuperState.READY:
            self.get_logger().info(f"superState: {self.superState}")
            if self.isFinished:
                self.get_logger().info("Mission finished, stopping")
                self.superState = SuperState.STOPPING
            elif self.asState == 2:
                self.get_logger().info("AS State is 2, starting mission")
                self.superState = SuperState.RUNNING
            
            
            

        elif self.superState == SuperState.RUNNING:
            self.get_logger().info(f"superState: {self.superState}")
            if self.isFinished:
                self.get_logger().info("Mission finished, stopping")
                self.superState = SuperState.STOPPING


        elif self.superState == SuperState.STOPPING:
            self.get_logger().info(f"superState: {self.superState}")
            self.get_logger().info(f"Current velocity: {self.currentVel}")
            if self.currentVel < self.maxStopVelTh:
                self.get_logger().info("Car stopped, finishing mission")
                self.superState = SuperState.FINISHED
                self.get_logger().info(f"superState: {self.superState}")


        elif self.superState == SuperState.FINISHED:
            if not self.shutdown_done:
                self.get_logger().info(f"calling mission launcher's shutdown")
                self.launcher.shutdown()
                self.shutdown_done = True

            self.isFinished = False
            self.superState = SuperState.WAITING
            self.amiState = CanState.AMI_NOT_SELECTED

           # self.get_logger().info("will sleep for 5 secs 😴😴😴😴😴")
            #time.sleep(5)
            #self.superState = SuperState.WAITING
            #self.amiState = CanState.AMI_NOT_SELECTED
            self.get_logger().info(f"mission shutdown complete back to waiting")



        #Publish
        self.publishRosCanMessages()

    def publishRosCanMessages(self) -> None:
        """
        Publishes the command to the car
        """

        if self.superState in (SuperState.WAITING, SuperState.LAUNCHING, SuperState.READY):
            self.missionFlagPub.publish(Bool(data = False))
            self.drivingFlagPub.publish(Bool(data = False))
        elif self.superState in (SuperState.RUNNING, SuperState.STOPPING) and self.asState == 2:
            self.missionFlagPub.publish(Bool(data = False))
            self.drivingFlagPub.publish(Bool(data = True))
        elif self.superState == SuperState.FINISHED:
            self.missionFlagPub.publish(Bool(data = True))
            self.drivingFlagPub.publish(Bool(data = False))

        self.cmd.publish(self.getCmdMessage())

    def getCmdMessage(self) -> AckermannDriveStamped:
        """
        Publishes the command to the car
        after changing the steer and vel
        msg to AckermannDriveStamped
        """
        cmdMsg = AckermannDriveStamped()
        if self.superState in (
            SuperState.WAITING,
            SuperState.LAUNCHING,
            SuperState.READY,
            SuperState.FINISHED,
        ):
            cmdMsg.drive.speed = 0.0
            cmdMsg.drive.steering_angle = 0.0
        elif self.superState == SuperState.RUNNING:
            cmdMsg.drive.speed = self.vel
            cmdMsg.drive.steering_angle = self.steer
        elif self.superState == SuperState.STOPPING:
            cmdMsg.drive.steering_angle = self.steer
            if self.currentVel > 0.1:
                targetVel = 0.5 * self.currentVel
            else:
                targetVel = 0.0
            cmdMsg.drive.speed = targetVel
        cmdMsg.header.stamp = self.get_clock().now().to_msg()
        return cmdMsg

    def canStateCallback(self, msg: CanState) -> None:
        """
        Callback to retreive the VCU's state and selected mission
        """
        #self.get_logger().info(f"Received CAN state message: {msg.as_state}")
        #self.get_logger().info(f"Received CAN state message: {msg.ami_state}")
        self.asState = msg.as_state
        #self.get_logger().info(f"🟢🟢🟢🟢🟢🟢🟢🟢 AS State: {self.asState}")
        self.amiState = msg.ami_state

        if self.amiState == 14:
            self.get_logger().info("AMI State: Trackdrive")
            self.create_subscription(
                Int16, self.loopClosureCountTopic, self.launcher.loopClosure_trackdrive_callback, 10
            )

    def isFinishedCallback(self, msg: Bool) -> None:
        """
        Callback for the mission's finished flag
        """
        self.get_logger().info(f"🟢🟢🟢🟢🟢🟢🟢🟢 Received isFinished message: {msg.data}")

        if msg.data:
            self.isFinished = True

    # def velCallback(self, msg: Float32) -> None:
    #     """
    #     Callback function for the velocity
    #     """
    #     self.get_logger().info(f"Received velocity message: {msg.data}")
    #     self.vel = msg.data

    # def steerCallback(self, msg: Float32) -> None:
    #     """
    #     Callback function for the steering angle
    #     """
    #     self.get_logger().info(f"Received steering message: {msg.data}")
    #     self.steer = msg.data

    def controlCallback(self, msg: AckermannDriveStamped) -> None:
        self.vel = msg.drive.speed  
        self.steer = msg.drive.steering_angle

    def currentVelCallback(self, msg: TwistWithCovarianceStamped) -> None:
        """
        Callback for the current velocity
        """
        #self.get_logger().info(f"Received current velocity message: {msg.twist.twist.linear.x}")
        self.currentVel = msg.twist.twist.linear.x


