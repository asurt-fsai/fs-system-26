import rclpy
from rclpy.node import Node

from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import PoseStamped

from tf2_ros import Buffer, TransformListener, LookupException, ExtrapolationException
import tf2_geometry_msgs  # for do_transform_pose

class ConeTransformer(Node):
    def __init__(self):
        super().__init__('cone_transformer_node')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.subscription = self.create_subscription(
            MarkerArray,
            '/carmaker/ObjectList',
            self.listener_callback,
            10)

        self.marker_pub = self.create_publisher(MarkerArray, '/cones_global_markers', 10)

    def listener_callback(self, msg: MarkerArray):
        try:
            marker_array = MarkerArray()
            marker_id = 0

            for marker in msg.markers:
                # Get frame of the marker
                frame_id = marker.header.frame_id

                # Filter out white cones by color approx (white = r=g=b=1 and alpha>0.9)
                c = marker.color
                if (abs(c.r - 1.0) < 0.1 and abs(c.g - 1.0) < 0.1 and abs(c.b - 1.0) < 0.1 and c.a > 0.9):
                    continue  # skip white cones

                # Lookup transform from marker frame to map
                transform = self.tf_buffer.lookup_transform(
                    'map',
                    frame_id,
                    rclpy.time.Time())

                # Create PoseStamped for the marker pose
                pose_local = PoseStamped()
                pose_local.header = marker.header
                pose_local.pose = marker.pose

                # Transform pose to map frame
                pose_global = tf2_geometry_msgs.do_transform_pose(pose_local, transform)

                # Create new marker with transformed pose
                new_marker = Marker()
                new_marker.header.frame_id = 'map'
                new_marker.header.stamp = self.get_clock().now().to_msg()
                new_marker.id = marker_id
                new_marker.type = Marker.SPHERE
                new_marker.action = Marker.ADD
                new_marker.pose = pose_global.pose
                new_marker.scale.x = 0.3
                new_marker.scale.y = 0.3
                new_marker.scale.z = 0.3
                new_marker.color = marker.color  # Keep original color
                new_marker.lifetime.sec = 0  # permanent

                marker_array.markers.append(new_marker)
                marker_id += 1

            self.marker_pub.publish(marker_array)

        except (LookupException, ExtrapolationException) as e:
            self.get_logger().warn(f"TF lookup failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ConeTransformer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
