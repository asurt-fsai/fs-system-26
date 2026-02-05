import rclpy
from rclpy.node import Node
from zed_msgs.msg import ObjectsStamped
from geometry_msgs.msg import Point
from asurt_msgs.msg import LandmarkArray, Landmark

# Constants for cone types
BLUE_CONE = 0
YELLOW_CONE = 1
ORANGE_CONE = 2
LARGE_CONE = 3
CONE_TYPE_UNKNOWN = 4

def convert_object_to_landmark(obj):
    """
    Convert a ZED Object to an `asurt_msgs/Landmark` message.
    """
    lm = Landmark()
    # Fill position (geometry_msgs/Point)
    try:
        lm.position.x = float(obj.position[0])
        lm.position.y = float(obj.position[1])
        lm.position.z = float(obj.position[2])
    except Exception:
        lm.position.x = 0.0
        lm.position.y = 0.0
        lm.position.z = 0.0

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
    # ZED confidence is typically 1-99 -> scale to 0.0-1.0
    lm.probability = float(getattr(obj, 'confidence', 0.0)) / 100.0

    return lm

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
        self.publisher = self.create_publisher(LandmarkArray, "/perception_landmarks", 10)
        self.message_count = 0
        self.landmarks = []  # List to store converted landmarks (for local use)

    def listener_callback(self, msg):
        # Convert each detected object to Landmark format and publish a LandmarkArray
        landmark_array = LandmarkArray()
        landmark_array.header = msg.header
        for obj in msg.objects:
            landmark = convert_object_to_landmark(obj)
            landmark_array.landmarks.append(landmark)
            self.landmarks.append(landmark)

        self.publisher.publish(landmark_array)
        self.message_count += 1
        self.get_logger().info(f"Published LandmarkArray from message {self.message_count}, total landmarks stored: {len(landmark_array.landmarks)}")
   

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