import rclpy
from rclpy.node import Node
from zed_msgs.msg import ObjectsStamped
from cone_mapping.msg import LandmarkArray, Landmark
from visualization_msgs.msg import MarkerArray, Marker
import math

# Constants for cone types
BLUE_CONE = 0
YELLOW_CONE = 1
ORANGE_CONE = 2
LARGE_CONE = 3
CONE_TYPE_UNKNOWN = 4

class Zed_to_Landmark(Node):
    def __init__(self):
        super().__init__('Zed_to_landmark')
        self.subscription = self.create_subscription(
            ObjectsStamped,
            '/zed/zed_node/obj_det/objects',
            self.listener_callback,
            10
        )
        # Publisher will send a LandmarkArray message containing all detected landmarks
        self.landmarks_publisher = self.create_publisher(LandmarkArray, "/perception/landmarks", 10)
        
        # Publisher for MarkerArray visualization
        self.marker_publisher = self.create_publisher(MarkerArray, "/perception_markers", 10)
        self.message_count = 0

    def listener_callback(self, msg):
        try:
            landmark_array = LandmarkArray()
            landmark_array.header = msg.header
            
            marker_array = MarkerArray()
            
            # Delete markers logic... (not implemented in snippet, assuming handled elsewhere or okay to omit if empty)

            for idx, obj in enumerate(msg.objects):
                try:
                    # --- CHANGE STARTS HERE ---
                    landmark = self.convert_object_to_landmark(obj)
                    
                    # If the object contained NaNs, we get None back. SKIP IT.
                    if landmark is None:
                        continue 
                        
                    landmark_array.landmarks.append(landmark)
                    # --- CHANGE ENDS HERE ---
                    
                    # Marker logic... (keep as is)
                    marker = self.convert_object_to_marker(obj, marker_id=idx, frame_id=msg.header.frame_id)
                    if marker:
                        marker.header = msg.header
                        marker_array.markers.append(marker)
                except Exception as e:
                    self.get_logger().warn(f"Error processing object {idx}: {e}")
                    continue

            self.landmarks_publisher.publish(landmark_array)
            self.marker_publisher.publish(marker_array)
            
        except Exception as e:
            self.get_logger().error(f"Error in listener_callback: {e}")
        # ... rest of function

    def convert_object_to_landmark(self, obj):
        """
        Convert a ZED Object to a `cone_mapping/Landmark` message.
        Returns None if the position contains NaNs or Infs.
        """
        # 1. SANITY CHECK: Check for NaNs before doing anything
        # ZED SDK returns nan if depth is invalid
        if not (math.isfinite(obj.position[0]) and 
                math.isfinite(obj.position[1]) and 
                math.isfinite(obj.position[2])):
            return None  # Reject this object entirely

        lm = Landmark()
        
        # 2. Safe assignment (we know they are finite now)
        lm.position.x = float(obj.position[0])
        lm.position.y = float(obj.position[1])
        lm.position.z = float(obj.position[2])

        # 3. Label Logic (Same as before)
        label = (obj.label or "").lower()
        if 'blue' in label:
            type_ = BLUE_CONE
        elif 'yellow' in label:
            type_ = YELLOW_CONE
        elif 'orange' in label:
            type_ = ORANGE_CONE
        elif 'large' in label:
            type_ = LARGE_CONE
        else:
            type_ = CONE_TYPE_UNKNOWN

        lm.type = int(type_)
        lm.identifier = int(getattr(obj, 'label_id', 0))
        lm.probability = float(getattr(obj, 'confidence', 0.0)) / 100.0

        return lm
    
    def convert_object_to_marker(self, obj, marker_id, frame_id="map"):
        """
        Convert a ZED Object to a visualization_msgs/Marker message.
        """
        marker = Marker()
        marker.header.frame_id = frame_id
        marker.id = marker_id
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        if not all(math.isfinite(float(p)) for p in obj.position):
            return None

        # Position
        try:
            marker.pose.position.x = float(obj.position[0])
            marker.pose.position.y = float(obj.position[1])
            marker.pose.position.z = float(obj.position[2])
        except Exception:
            marker.pose.position.x = 0.0
            marker.pose.position.y = 0.0
            marker.pose.position.z = 0.0

        # Orientation (no rotation for sphere)
        marker.pose.orientation.w = 1.0

        marker.header.stamp = self.get_clock().now().to_msg()

        # Scale
        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0

        # Color based on cone type
        label = (obj.label or "").lower()
        if 'blue' in label:
            marker.color.r = 0.0
            marker.color.g = 0.0
            marker.color.b = 1.0
        elif 'yellow' in label:
            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 0.0
        elif 'orange' in label:
            marker.color.r = 1.0
            marker.color.g = 0.65
            marker.color.b = 0.0
        elif 'large' in label:
            marker.color.r = 0.5
            marker.color.g = 0.5
            marker.color.b = 0.5
        else:
            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 1.0

        marker.color.a = 1.0  # Alpha

        return marker

def main(args=None):
    rclpy.init(args=args)

    node = Zed_to_Landmark()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node interrupted by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()