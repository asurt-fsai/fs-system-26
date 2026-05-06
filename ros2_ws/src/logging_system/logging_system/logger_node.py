# logger_node.py
import rclpy
from rclpy.node import Node
from asurt_msgs.msg import Event
import json

class LoggerNode(Node):
    def __init__(self):
        super().__init__('logger_node')

        self.subscription = self.create_subscription(
            Event,
            '/logging/events',
            self.callback,
            10
        )

        self.file = open("./logging_debug/events_log.json", "a")

    def callback(self, msg):
        event = {
            "timestamp": msg.stamp.sec + msg.stamp.nanosec * 1e-9,
            "severity": msg.severity,
            "category": msg.category,
            "event_type": msg.event_type,
            "source": msg.source,
            "details": json.loads(msg.details_json)
        }

        self.file.write(json.dumps(event) + "\n")
        self.file.flush()

def main():
    rclpy.init()
    node = LoggerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
