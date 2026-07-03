#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, Float32

from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray


class OdomLoopClosureNode(Node):

    def __init__(self):
        super().__init__('odom_loop_closure_node')

        # ==========================
        # Parameters
        # ==========================

        self.min_travel_distance = 10.0   # meters; keep this small enough for first-lap detection
        self.start_radius = 1.5          # meters

        # ==========================
        # State
        # ==========================

        self.start_pose = None
        self.previous_pose = None

        self.travelled_distance = 0.0
        self.has_moved = False

        self.previous_loop_condition = False

        # ==========================
        # Subscribers
        # ==========================

        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/zed/zed_node/pose',
            self.pose_callback,
            10
        )

        # ==========================
        # Publishers
        # ==========================

        self.distance_pub = self.create_publisher(
            Float32,
            '/slam/distance',
            10
        )

        self.loop_closure_pub = self.create_publisher(
            Bool,
            '/loop_closure_flag',
            10
        )

        self.start_pose_pub = self.create_publisher(
            PoseStamped,
            '/start_pose',
            10
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/loop_closure_markers',
            10
        )

        self.get_logger().info(
            'Odom loop closure node started'
        )

    def pose_callback(self, msg: PoseStamped):

        current_pose = msg.pose

        # ==========================
        # Initialize start pose
        # ==========================

        if self.start_pose is None:

            self.start_pose = current_pose
            self.previous_pose = current_pose

            start_msg = PoseStamped()
            start_msg.header = msg.header
            start_msg.pose = self.start_pose

            self.start_pose_pub.publish(start_msg)

            self.get_logger().info(
                'Start pose initialized'
            )

            return

        # ==========================
        # Distance accumulation
        # ==========================

        dx = (
            current_pose.position.x -
            self.previous_pose.position.x
        )

        dy = (
            current_pose.position.y -
            self.previous_pose.position.y
        )

        self.travelled_distance += math.hypot(dx, dy)
        if self.travelled_distance > 0.0:
            self.has_moved = True

        self.previous_pose = current_pose

        # ==========================
        # Publish distance
        # ==========================

        distance_msg = Float32()
        distance_msg.data = float(self.travelled_distance)

        self.distance_pub.publish(distance_msg)

        # ==========================
        # Loop closure condition
        # ==========================

        current_condition = self.check_loop_closure(
            current_pose
        )

        loop_event = (
            current_condition
            and not self.previous_loop_condition
        )
        if loop_event:
            self.get_logger().info("Loop Closure Detected!!!!!")

        self.previous_loop_condition = current_condition

        loop_msg = Bool()
        loop_msg.data = loop_event

        self.loop_closure_pub.publish(loop_msg)

        # ==========================
        # RViz markers
        # ==========================

        self.publish_markers(
            msg,
            current_condition
        )

    def check_loop_closure(self, current_pose):

        if not self.has_moved:
            return False

        if self.travelled_distance < self.min_travel_distance:
            return False

        dx = (
            current_pose.position.x -
            self.start_pose.position.x
        )

        dy = (
            current_pose.position.y -
            self.start_pose.position.y
        )

        distance_to_start = math.hypot(dx, dy)

        return distance_to_start < self.start_radius

    def publish_markers(
        self,
        pose_msg,
        loop_closed
    ):

        markers = MarkerArray()

        # ===================================
        # Marker 0: Start Pose
        # ===================================

        start_marker = Marker()

        start_marker.header = pose_msg.header
        start_marker.header.frame_id = "zed_left_camera_frame"

        start_marker.ns = "loop_closure"
        start_marker.id = 0

        start_marker.type = Marker.SPHERE
        start_marker.action = Marker.ADD

        start_marker.pose.position = (
            self.start_pose.position
        )

        start_marker.scale.x = 1.0
        start_marker.scale.y = 1.0
        start_marker.scale.z = 1.0

        start_marker.color.a = 1.0
        start_marker.color.g = 1.0

        markers.markers.append(start_marker)

        # ===================================
        # Marker 1: Closure Radius
        # ===================================

        radius_marker = Marker()

        radius_marker.header = pose_msg.header
        radius_marker.header.frame_id = "zed_left_camera_frame"

        radius_marker.ns = "loop_closure"
        radius_marker.id = 1

        radius_marker.type = Marker.CYLINDER
        radius_marker.action = Marker.ADD

        radius_marker.pose.position = (
            self.start_pose.position
        )

        radius_marker.scale.x = (
            self.start_radius * 2
        )

        radius_marker.scale.y = (
            self.start_radius * 2
        )

        radius_marker.scale.z = 0.1

        radius_marker.color.a = 0.2
        radius_marker.color.g = 1.0

        markers.markers.append(radius_marker)

        # ===================================
        # Marker 2: Current Vehicle
        # ===================================

        vehicle_marker = Marker()

        vehicle_marker.header = pose_msg.header
        vehicle_marker.header.frame_id = "zed_left_camera_frame"

        vehicle_marker.ns = "loop_closure"
        vehicle_marker.id = 2

        vehicle_marker.type = Marker.SPHERE
        vehicle_marker.action = Marker.ADD

        vehicle_marker.pose.position = (
            pose_msg.pose.position
        )

        vehicle_marker.scale.x = 0.5
        vehicle_marker.scale.y = 0.5
        vehicle_marker.scale.z = 0.5

        vehicle_marker.color.a = 1.0
        vehicle_marker.color.b = 1.0
        vehicle_marker.color.r = 1.0

        markers.markers.append(vehicle_marker)

        # ===================================
        # Marker 3: Status Text
        # ===================================

        text_marker = Marker()

        text_marker.header = pose_msg.header
        text_marker.header.frame_id = "zed_left_camera_frame"

        text_marker.ns = "loop_closure"
        text_marker.id = 3

        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD

        text_marker.pose.position = (
            pose_msg.pose.position
        )

        text_marker.pose.position.z += 2.0

        text_marker.scale.z = 0.8

        text_marker.color.a = 1.0
        text_marker.color.r = 1.0
        text_marker.color.g = 1.0
        text_marker.color.b = 1.0

        if loop_closed:
            text_marker.text = "LOOP CLOSED"
        else:
            text_marker.text = (
                f"{self.travelled_distance:.1f} m"
            )

        markers.markers.append(text_marker)

        self.marker_pub.publish(markers)


def main(args=None):

    rclpy.init(args=args)

    node = OdomLoopClosureNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()