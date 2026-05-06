import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from asurt_msgs.msg import Event
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Path
from collections import deque
import json


class FrequencyTracker:
    def __init__(self, node, window_size=20):
        self.timestamps = deque(maxlen=window_size)
        self.node = node

    def tick(self):
        self.timestamps.append(self.node.get_clock().now())

    def get_frequency(self):
        if len(self.timestamps) < 2:
            return 0.0
        
        # Convert ROS Duration to seconds
        dt_ns = (self.timestamps[-1] - self.timestamps[0]).nanoseconds
        dt = dt_ns / 1e9
        return (len(self.timestamps) - 1) / dt if dt > 0 else 0.0
   

class TopicMonitor(Node):
    def __init__(self):
        super().__init__('topic_monitor')
        
        # Message type mapping
        self.message_types = {
            "MarkerArray": MarkerArray,
            "Path": Path,
        }
        
        # Parameters
        self.declare_parameter('topics')
        self.declare_parameter('expected_freq', '{}')
        self.declare_parameter('topic_types', '{}')
        self.declare_parameter('timeout', 5.0)
        
        self.topic_names = self.get_parameter('topics').get_parameter_value().string_array_value
        
        # Parse expected frequencies
        expected_freq_json = self.get_parameter('expected_freq').value
        try:
            self.expected_freqs = json.loads(expected_freq_json)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Invalid JSON for expected_freq: {expected_freq_json}. Using defaults.")
            self.expected_freqs = {}
        
        # Parse topic types
        topic_types_json = self.get_parameter('topic_types').value
        try:
            self.topic_types = json.loads(topic_types_json)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Invalid JSON for topic_types: {topic_types_json}. Using defaults.")
            self.topic_types = {}
        
        self.timeout = self.get_parameter('timeout').value
        
        # Initialize topic tracking: topic_name -> [last_time, count, crashed, expected_freq, timeout]
        self.topics = {}
        self.trackers = {}
        self.low_freq_counters = {}
        
        # Create subscriptions and trackers for each topic
        for topic in self.topic_names:
            expected_freq = self.expected_freqs.get(topic, 10.0)
            topic_type_str = self.topic_types.get(topic)
            
            if topic_type_str not in self.message_types:
                self.get_logger().error(f"Unknown message type '{topic_type_str}' for topic '{topic}'")
                continue
                
            msg_type = self.message_types[topic_type_str]
            
            # Initialize tracking
            self.topics[topic] = [None, 0, False, expected_freq, self.timeout]
            self.trackers[topic] = FrequencyTracker(self)
            self.low_freq_counters[topic] = 0
            
            # Create subscription
            self.create_subscription(msg_type, topic, self.create_callback(topic), 10)
            
            self.get_logger().info(f"Monitoring topic '{topic}' with expected freq {expected_freq}Hz, type {topic_type_str}")
        
        self.pub = self.create_publisher(Event, '/logging/events', 10)
        self.timer = self.create_timer(1.0, self.check)
    
    def get_time(self):
        ns = self.get_clock().now().nanoseconds
        return ns / 1e9
    
    def create_callback(self, topic_name):
        """Create a callback function for the given topic"""
        def callback(msg):
            self.trackers[topic_name].tick()
            now = self.get_time()
            last_time, count, crashed, expected_freq, timeout = self.topics[topic_name]
            
            if crashed:
                self.topics[topic_name] = [now, 1, False, expected_freq, timeout]
                self.publish_event("NODE_RESUMED", {"topic": topic_name})
                return
            
            if last_time is None:
                self.topics[topic_name] = [now, 1, False, expected_freq, timeout]
            else:
                self.topics[topic_name] = [now, count + 1, False, expected_freq, timeout]
            
            # Perception-specific checks
            if topic_name == "/perception_markers":
                self.check_perception_data(msg)
        
        return callback
    
    def check_perception_data(self, msg):
        """Perception-specific data validation checks"""
        unknown_found = False
        cone_count = 0

        for marker in msg.markers:
            if marker.action == marker.DELETEALL:
                continue

            cone_count += 1

            # White color represents unknown cone
            if (marker.color.r == 1.0 and
                marker.color.g == 1.0 and
                marker.color.b == 1.0):
                unknown_found = True

        if unknown_found:
            self.publish_event("INVALID_DATA", {
                "topic": "/perception_markers",
                "detail": "unknown cone"
            })
        
        if hasattr(self, "prev_cone_count"):
            if (cone_count > 10) and (cone_count >= 2 * self.prev_cone_count):
                self.publish_event("INVALID_DATA", {
                    "topic": "/perception_markers",
                    "detail": "possible hallucination"
                })

        self.prev_cone_count = cone_count

    
    def check(self):
        now = self.get_time()
        
        for topic, (last_time, count, crashed, expected_freq, timeout) in self.topics.items():
            if crashed:
                continue
            
            if last_time is None:
                continue
            
            dt = now - last_time
            
            if dt > timeout:
                self.topics[topic] = [last_time, count, True, expected_freq, timeout]
                self.publish_event("NODE_CRASH", {
                    "topic": topic,
                    "silence_seconds": round(dt, 2),
                    "timeout": timeout
                })
                continue
            
            freq = self.trackers[topic].get_frequency()
            
            if freq < expected_freq * 0.5 and self.low_freq_counters[topic] == 0:
                self.publish_event("LOW_FREQ", {
                    "topic": topic,
                    "freq": round(freq, 2),
                    "expected": expected_freq
                })
                self.low_freq_counters[topic] = 1
            elif freq >= expected_freq * 0.5:
                self.low_freq_counters[topic] = 0
            elif self.low_freq_counters[topic] < 3:
                self.low_freq_counters[topic] += 1
    
    def publish_event(self, event_type, details):
        msg = Event()
        msg.stamp = self.get_clock().now().to_msg()
        msg.severity = "ERROR" if event_type == "NODE_CRASH" else "WARN"
        msg.category = "TOPIC_HEALTH"
        msg.event_type = event_type
        msg.source = "topic_monitor"
        msg.details_json = json.dumps(details)
        self.pub.publish(msg)
        self.get_logger().info(f"{event_type}: {details}")

def main():
    rclpy.init()
    node = TopicMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
