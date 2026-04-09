import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import message_filters

class TestSync(Node):
    def __init__(self):
        super().__init__('test_sync')
        self.sub = self.create_subscription(Odometry, '/aft_mapped_to_init', self.cb, 10)
    def cb(self, msg):
        self.get_logger().info('Got odom')

rclpy.init()
n = TestSync()
rclpy.spin_once(n, timeout_sec=1.0)
