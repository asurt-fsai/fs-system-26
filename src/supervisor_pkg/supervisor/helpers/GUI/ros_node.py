import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.msg import CanState

class ROSNode(Node):
    def __init__(self, gui_cb):
        super().__init__("gui_node")

        self.gui_cb = gui_cb

        self.create_subscription(
            AckermannDriveStamped,
            "/cmd",
            self.cmd_cb,
            10
        )

        self.create_subscription(
            AckermannDriveStamped,
            "/control",
            self.cmd_cb,
            10
        )

        self.create_subscription(
            CanState,
            "/ros_can/state",
            self.state_cb,
            10
        )

        self.create_subscription(
            String,
            "/static_mission/state",
            self.mission_state_cb,
            10
        )

    def cmd_cb(self, msg):
        vel = round(msg.drive.speed, 2)
        steer = round(msg.drive.steering_angle, 2)
        # Display steering in degrees for readability
        #steer = round(steer * 57.2958, 2)
        self.gui_cb("cmd", vel, steer)

    def state_cb(self, msg):
        self.gui_cb("state", msg.as_state)

    def mission_state_cb(self, msg):
        self.gui_cb("mission_state", msg.data)