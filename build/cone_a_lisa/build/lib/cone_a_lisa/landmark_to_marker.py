#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from asurt_msgs.msg import LandmarkArray
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA

# ========================
# Cone Type Constants (manual copy from .msg)
# ========================
BLUE_CONE = 0
YELLOW_CONE = 1
ORANGE_CONE = 2
LARGE_CONE = 3
CONE_TYPE_UNKNOWN = 4


class LandmarkVisualizer(Node):
    def __init__(self):
        super().__init__('landmark_visualizer')
        
        # Subscriber to the LandmarkArray topic
        self.subscription = self.create_subscription(
            LandmarkArray,
            '/Landmarks/Observed',
            self.landmarkCallback,
            10
        )
        
        # Publisher for the MarkerArray for RViz
        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/landmark_markers',
            10
        )
        
        self.get_logger().info("Landmark Visualizer Node Started")

    def landmarkCallback(self, msg):
        marker_array = MarkerArray()
        
        for i, landmark in enumerate(msg.landmarks):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "landmarks"
            marker.id = i
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD

            # Set position
            marker.pose.position.x = landmark.position.x
            marker.pose.position.y = landmark.position.y
            marker.pose.position.z = landmark.position.z
            #marker.pose.orientation.w = 1.0

            # Set size
            marker.scale.x = 0.5
            marker.scale.y = 0.5
            marker.scale.z = 0.8

            # Set color based on type
            if landmark.type == BLUE_CONE:
                marker.color = ColorRGBA(r=0.0, g=0.0, b=1.0, a=1.0)  # Blue
            elif landmark.type == YELLOW_CONE:
                marker.color = ColorRGBA(r=1.0, g=1.0, b=0.0, a=1.0)  # Yellow
            elif landmark.type == ORANGE_CONE:
                marker.color = ColorRGBA(r=1.0, g=0.5, b=0.0, a=1.0)  # Orange
            elif landmark.type == LARGE_CONE:
                marker.color = ColorRGBA(r=1.0, g=0.0, b=1.0, a=1.0)  # Magenta for large
            else:  # CONE_TYPE_UNKNOWN or invalid
                marker.color = ColorRGBA(r=0.5, g=0.5, b=0.5, a=1.0)  # Gray
            
            marker.lifetime.sec = 1
            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = LandmarkVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
