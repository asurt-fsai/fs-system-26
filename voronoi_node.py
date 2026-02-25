#!/usr/bin/env python3
"""
Voronoi Path Planning ROS2 Node

Subscribes to cone detections (MarkerArray) and odometry (Odometry),
runs the Voronoi-based path planner, and publishes the resulting path.
"""

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import Pose, PoseStamped
import numpy as np
from tf_transformations import euler_from_quaternion
from tf_helper.StatusPublisher import StatusPublisher
from tf_helper.TFHelper import TFHelper

from path_planning.modules.planner import PathPlanner


class VoronoiPlanningNode(Node):
    """
    ROS2 node that wraps the Voronoi-based path planner.

    Subscriptions:
        - Cones (MarkerArray): Cone positions + colors from perception/SLAM.
        - Odometry (Odometry): Car pose from localization.

    Publishers:
        - Path (nav_msgs/Path): The planned path for control.
    """

    def __init__(self) -> None:
        super().__init__("voronoi_planning_node")
        self.get_logger().info("Voronoi Path Planner node starting...")

        # State
        self.cone_data: list = []  # [(x, y, color_str), ...]
        self.car_position = np.array([0.0, 0.0])
        self.car_yaw: float = 0.0
        self.odom_received: bool = False

        # Parameters
        self._declare_params()
        self._load_params()

        # Pub / Sub
        self._init_pub_sub()

        # TF helper for frame transforms
        self.tf_helper = TFHelper(self)

        self.get_logger().info("Voronoi Path Planner node ready.")

    # ------------------------------------------------------------------
    # Parameter handling
    # ------------------------------------------------------------------
    def _declare_params(self) -> None:
        """Declare all ROS2 parameters with sensible defaults."""
        # Planner tuning
        self.declare_parameter("voronoi.planner.robot_radius", 0.7)
        self.declare_parameter("voronoi.planner.safety_margin", 0.4)
        self.declare_parameter("voronoi.planner.max_edge_len", 8.0)

        # Topics
        self.declare_parameter("voronoi.topics.frame_id", "map")
        self.declare_parameter("voronoi.topics.path_topic", "/planning/path")
        self.declare_parameter("voronoi.topics.odometry_topic", "/odometry/filtered")
        self.declare_parameter("voronoi.topics.cones_topic", "/slam/cones")

    def _load_params(self) -> None:
        """Read declared parameters and initialise the planner."""
        robot_radius = self.get_parameter(
            "voronoi.planner.robot_radius"
        ).get_parameter_value().double_value
        safety_margin = self.get_parameter(
            "voronoi.planner.safety_margin"
        ).get_parameter_value().double_value
        max_edge_len = self.get_parameter(
            "voronoi.planner.max_edge_len"
        ).get_parameter_value().double_value

        self.frame_id = self.get_parameter(
            "voronoi.topics.frame_id"
        ).get_parameter_value().string_value

        self.planner = PathPlanner(
            robot_radius=robot_radius,
            safety_margin=safety_margin,
            max_edge_len=max_edge_len,
        )
        self.get_logger().info(
            f"Planner config: robot_radius={robot_radius}, "
            f"safety_margin={safety_margin}, max_edge_len={max_edge_len}"
        )

    # ------------------------------------------------------------------
    # Publishers & Subscribers
    # ------------------------------------------------------------------
    def _init_pub_sub(self) -> None:
        """Create publishers and subscribers."""
        path_topic = self.get_parameter(
            "voronoi.topics.path_topic"
        ).get_parameter_value().string_value
        odometry_topic = self.get_parameter(
            "voronoi.topics.odometry_topic"
        ).get_parameter_value().string_value
        cones_topic = self.get_parameter(
            "voronoi.topics.cones_topic"
        ).get_parameter_value().string_value

        self.path_publisher = self.create_publisher(Path, path_topic, 10)

        self.cone_subscriber = self.create_subscription(
            MarkerArray, cones_topic, self._cones_callback, 10
        )
        self.odom_subscriber = self.create_subscription(
            Odometry, odometry_topic, self._odom_callback, 10
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _cones_callback(self, msg: MarkerArray) -> None:
        """
        Convert incoming MarkerArray into the planner's cone format
        and trigger path planning.

        Cone color classification (by RGB):
            - Yellow cone: g > 0.8
            - Blue cone:   b > 0.8, g < 0.4, r < 0.4
            - White cones (r,g,b > 0.95) are skipped.
            - Everything else is treated as unknown and skipped.
        """
        self.cone_data = []

        for marker in msg.markers:
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            x, y = marker.pose.position.x, marker.pose.position.y

            # Skip white / artifact markers
            if r > 0.95 and g > 0.95 and b > 0.95:
                continue

            if g > 0.8:  # Yellow
                self.cone_data.append((x, y, "y"))
            elif b > 0.8 and g < 0.4 and r < 0.4:  # Blue
                self.cone_data.append((x, y, "b"))
            # Unknown / orange cones are ignored for the Voronoi planner
            # since it only operates on yellow ('y') and blue ('b') pairs.

        yellow_count = sum(1 for c in self.cone_data if c[2] == 'y')
        blue_count = sum(1 for c in self.cone_data if c[2] == 'b')
        self.get_logger().info(
            f"Cones received: {len(self.cone_data)} total "
            f"(Y={yellow_count}, B={blue_count})"
        )

        self._plan_and_publish()

    def _odom_callback(self, msg: Odometry) -> None:
        """Extract car position and yaw from odometry."""
        pose = msg.pose.pose
        self.car_position = np.array([pose.position.x, pose.position.y])

        q = pose.orientation
        (_, _, yaw) = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.car_yaw = yaw
        self.odom_received = True

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def _plan_and_publish(self) -> None:
        """Run the Voronoi planner and publish the resulting path."""
        if not self.odom_received:
            self.get_logger().warn(
                "No odometry received yet — using default pose (0, 0, 0).",
                throttle_duration_sec=5.0,
            )

        # Build car_data in the format the planner expects: [(x, y, yaw)]
        car_data = [(
            float(self.car_position[0]),
            float(self.car_position[1]),
            float(self.car_yaw),
        )]

        self.get_logger().info(
            f"Planning with car_pos=({car_data[0][0]:.2f}, {car_data[0][1]:.2f}), "
            f"yaw={car_data[0][2]:.2f}, cones={len(self.cone_data)}"
        )

        try:
            path_points = self.planner.execute_cycle(self.cone_data, car_data)
        except Exception as e:
            self.get_logger().error(f"Planner crashed: {type(e).__name__}: {e}")
            return

        if not path_points:
            self.get_logger().warn("Planner returned empty path.")
            return

        # Build nav_msgs/Path
        timestamp = self.get_clock().now().to_msg()
        path_msg = Path()
        path_msg.header.stamp = timestamp
        path_msg.header.frame_id = self.frame_id

        for px, py in path_points:
            pose = Pose()
            pose.position.x = float(px)
            pose.position.y = float(py)

            pose_stamped = PoseStamped()
            pose_stamped.pose = pose
            pose_stamped.header.stamp = timestamp
            pose_stamped.header.frame_id = self.frame_id

            path_msg.poses.append(pose_stamped)

        self.path_publisher.publish(path_msg)
        self.get_logger().info(f"Published path with {len(path_msg.poses)} poses.")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Initialise ROS2, spin the node, then shut down."""
    rclpy.init()
    node = VoronoiPlanningNode()
    status = StatusPublisher("/status/voronoi_planning_node", node)

    status.starting()
    status.ready()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
