#!/usr/bin/env python3
"""
Pose Republisher
Subscribes to `/zed/zed_node/pose` and republishes the same `PoseStamped`
on `/cone_mapping/pose`. Useful as a simple shim for downstream nodes.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped


class PoseRepublisher(Node):
    def __init__(self):
        super().__init__('pose_republisher')

        # Parameters (can be overridden via ros2 param or remap)
        self.declare_parameter('input_topic', '/zed/zed_node/pose')
        self.declare_parameter('output_topic', '/pose_republisher/pose')

        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.pub = self.create_publisher(PoseStamped, output_topic, 10)
        self.sub = self.create_subscription(PoseStamped, input_topic, self.cb_pose, 10)

        self.get_logger().info(f'PoseRepublisher: {input_topic} -> {output_topic}')

    def cb_pose(self, msg: PoseStamped):
        # For now, simply republish the incoming pose unchanged
        try:
            self.pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f'Failed to publish pose: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = PoseRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
