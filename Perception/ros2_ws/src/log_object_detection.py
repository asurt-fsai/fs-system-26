import rclpy
from rclpy.node import Node
from zed_msgs.msg import ObjectsStamped
import sys
import yaml
import numpy as np
from rosidl_runtime_py.convert import message_to_ordereddict

def to_yaml_safe(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_yaml_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_yaml_safe(v) for v in obj]
    return obj

class ObjectDetectionLogger(Node):
    def __init__(self, log_file_path):
        super().__init__('object_detection_logger')
        self.subscription = self.create_subscription(
            ObjectsStamped,
            '/zed/zed_node/obj_det/objects',
            self.listener_callback,
            10
        )
        self.log_file_path = log_file_path
        self.message_count = 0
        self.max_messages = 5
        self.log_file = open(self.log_file_path, 'w')
        self.get_logger().info(f"Logging to {self.log_file_path}")

    def listener_callback(self, msg):
        if self.message_count < self.max_messages:
            msg_dict = message_to_ordereddict(msg)
            msg_dict = to_yaml_safe(msg_dict)

            yaml.safe_dump(
                msg_dict,
                self.log_file,
                explicit_start=True,  
                sort_keys=False
            )

            self.message_count += 1
            self.get_logger().info(f"Logged message {self.message_count}")

        
        if self.message_count >= self.max_messages:
            self.get_logger().info("Logged 5 messages. Shutting down.")
            self.log_file.close()
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) < 2:
        print("Usage: ros2 run <package_name> log_object_detection.py <log_file_path>")
        return

    log_file_path = sys.argv[1]
    node = ObjectDetectionLogger(log_file_path)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node interrupted by user.")
    finally:
        node.log_file.close()
        node.destroy_node()

if __name__ == '__main__':
    main()