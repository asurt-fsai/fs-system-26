import yaml
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import Header
from asurt_msgs.msg import LandmarkArray, Landmark  # Ensure this package is installed

class LandmarkToMarkerArray(Node):
    def __init__(self):
        super().__init__('cones_marker_publisher')

        # Publisher for MarkerArray
        self.marker_pub = self.create_publisher(MarkerArray, '/visualization_marker_array', 10)

        # Subscriber to the /AirSim/Topic/cones topic
        self.cone_sub = self.create_subscription(
            LandmarkArray,
            '/AirSim/Topic/cones',
            self.cone_callback,
            10)

        self.get_logger().info("LandmarkToMarkerArray Node Started...")

    def cone_callback(self, msg):
        marker_array = MarkerArray()

        for i, landmark in enumerate(msg.landmarks):
            marker = self.convert_to_marker(landmark, i)
            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)
        self.get_logger().info(f"Published {len(msg.landmarks)} markers.")

    def convert_to_marker(self, landmark, marker_id):
        marker = Marker()
        marker.header = Header()
        marker.header.frame_id = "map"  # Change if necessary
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "cones"
        marker.id = marker_id
        marker.type = Marker.SPHERE  # Change to CYLINDER or CUBE if preferred
        marker.action = Marker.ADD
        marker.pose.position = Point(x=landmark.position.x, y=landmark.position.y, z=landmark.position.z)
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.3
        marker.scale.y = 0.3
        marker.scale.z = 0.3

        # Set color based on cone type
        if landmark.type == Landmark.BLUE_CONE:
            marker.color.r = 0.0
            marker.color.g = 0.0
            marker.color.b = 1.0
        elif landmark.type == Landmark.YELLOW_CONE:
            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 0.0
        elif landmark.type == Landmark.ORANGE_CONE:
            marker.color.r = 1.0
            marker.color.g = 0.5
            marker.color.b = 0.0
        elif landmark.type == Landmark.LARGE_CONE:
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
        else:  # UNKNOWN TYPE
            marker.color.r = 0.5
            marker.color.g = 0.5
            marker.color.b = 0.5

        marker.color.a = 1.0  # Fully visible
        return marker

def main(args=None):
    rclpy.init(args=args)
    node = LandmarkToMarkerArray()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down node")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
