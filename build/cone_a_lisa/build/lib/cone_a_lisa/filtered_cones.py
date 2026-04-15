import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray, Marker
from builtin_interfaces.msg import Duration

class WhiteConeFilterNode(Node):
    def __init__(self):
        super().__init__('white_cone_filter_node')
        self.create_subscription(MarkerArray, '/carmaker/ObjectList', self.marker_callback, 10)
        self.filtered_pub = self.create_publisher(MarkerArray, '/filtered/ObjectList', 10)

    def marker_callback(self, msg):
        filtered_markers = MarkerArray()
        marker_id = 0

        for marker in msg.markers:
            # Only keep non-white cones
            if not (marker.color.r == 1.0 and marker.color.g == 1.0 and marker.color.b == 1.0):
                new_marker = Marker()
                new_marker.header.frame_id = 'map'
                new_marker.header.stamp = self.get_clock().now().to_msg()
                new_marker.ns = "filtered_cones"
                new_marker.id = marker_id
                new_marker.type = marker.type
                new_marker.action = Marker.ADD
                new_marker.pose = marker.pose
                new_marker.scale = marker.scale
                new_marker.color = marker.color
                new_marker.lifetime = Duration(sec=1)
                filtered_markers.markers.append(new_marker)
                marker_id += 1

        # Publish the filtered markers
        if filtered_markers.markers:
            self.filtered_pub.publish(filtered_markers)

def main(args=None):
    rclpy.init(args=args)
    node = WhiteConeFilterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
