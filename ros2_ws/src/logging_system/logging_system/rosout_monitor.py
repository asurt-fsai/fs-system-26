# rosout_monitor_node.py
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import Log
from asurt_msgs.msg import Event
import json

class RosoutMonitor(Node):
    def __init__(self):
        super().__init__('rosout_monitor')

        self.sub = self.create_subscription(
            Log,
            '/rosout',
            self.callback,
            10
        )

        self.pub = self.create_publisher(Event, '/logging/events', 10)

    def callback(self, msg):
        if ("topic_monitor" in msg.name) or ("resource_monitor" in msg.name) or ("rosout_monitor" in msg.name):
            return
        #self.get_logger().info(f"Level type: {type(msg.level)}, value: {msg.level}")
        warn_level = int.from_bytes(Log.WARN, byteorder='little')
        error_level = int.from_bytes(Log.ERROR, byteorder='little')
        level = msg.level
        #self.get_logger().info(f"msg level: {level}")
        # Keywords to detect in lower-level messages
        error_keywords = ['error', 'crash', 'disconnected', 'failed', 'exception']

        # Check if level is below WARN
        if level < warn_level:
            # Check message content for error keywords
            msg_lower = msg.msg.lower()
            if not any(keyword in msg_lower for keyword in error_keywords):
                return

        event = Event()
        event.stamp = msg.stamp
        event.severity = "ERROR" if level >= error_level else "WARN"
        event.category = "NODE_HEALTH"
        event.event_type = "NODE_LOG"
        event.source = msg.name
        event.details_json = json.dumps({
            "message": msg.msg,
            "file": msg.file,
            "line": msg.line
        })

        self.pub.publish(event)

def main():
    rclpy.init()
    node = RosoutMonitor()
    rclpy.spin(node)
    rclpy.shutdown()
