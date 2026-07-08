import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64
import math

class OdomTracker(Node):
    def __init__(self):
        super().__init__('odom_tracker')

        # Subscriber to odometry topic
        self.subscription = self.create_subscription(
            Odometry,
            '/aft_mapped_adjusted',
            self.listener_callback,
            10
        )

        # Publishers for distance and velocity
        self.distance_pub = self.create_publisher(Float64, '/slam/distance', 10)
        self.velocity_pub = self.create_publisher(Float64, '/slam/velocity', 10)

        # Internal state
        self.prev_x = None
        self.prev_y = None
        self.total_distance = 0.0

    def listener_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self.prev_x is not None and self.prev_y is not None:
            dx = x - self.prev_x
            dy = y - self.prev_y
            step_distance = math.sqrt(dx ** 2 + dy ** 2)
            self.total_distance += step_distance

            velocity = math.sqrt(
                msg.twist.twist.linear.x ** 2 +
                msg.twist.twist.linear.y ** 2
            )

            # Publish distance and velocity
            distance_msg = Float64()
            distance_msg.data = self.total_distance
            self.distance_pub.publish(distance_msg)

            velocity_msg = Float64()
            velocity_msg.data = velocity
            self.velocity_pub.publish(velocity_msg)

        # Save current position for next loop
        self.prev_x = x
        self.prev_y = y


def main(args=None):
    rclpy.init(args=args)
    node = OdomTracker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
