#!/usr/bin/env python3
"""
Voronoi Path Planning ROS2 Node
This node is responsible for starting the Voronoi-based path planning module.
"""

import threading
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import Pose, PoseStamped
import numpy as np
from tf_transformations import euler_from_quaternion
from tf_helper.StatusPublisher import StatusPublisher

from path_planning.modules.planner import PathPlanner


class VoronoiPlanningNode(Node):
    """
    A ROS2 node for Voronoi-based path planning.

    Receives cone positions from perception and car odometry from localization,
    computes a path using the Voronoi planner, and publishes it for control.

    Attributes:
        path (list): The calculated path as a list of (x, y) tuples.
        cone_data (list): Cone positions as (x, y, color) tuples.
        carPosition (np.ndarray): The position of the car [x, y].
        carDirection (float): The yaw angle of the car in radians.
    """

    def __init__(self) -> None:
        super().__init__("voronoi_planning_node")
        self.get_logger().info("Voronoi Path Planner instantiated...")
        self.path = []
        self.cone_data = []
        self.carPosition = np.array([0.0, 0.0])
        self.carDirection = np.float_(0.0)

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()

    def declareParameters(self) -> None:
        """
        Declare the ROS2 parameters for the Voronoi planning node.
        """
        self.declare_parameter("planning.voronoi.robot_radius", 0.7)
        self.declare_parameter("planning.voronoi.safety_margin", 0.4)
        self.declare_parameter("planning.voronoi.max_edge_len", 8.0)

        self.declare_parameter("planning.topics.frame_id", "map")
        self.declare_parameter("planning.topics.pathTopic", "/planning/path")
        self.declare_parameter("planning.topics.odometryTopic", "/odometry")
        self.declare_parameter("planning.topics.conesTopic", "/cones")

    def setParameters(self) -> None:
        """
        Read parameters from the parameter server and initialize the planner.
        """
        robot_radius = (
            self.get_parameter("planning.voronoi.robot_radius")
            .get_parameter_value().double_value
        )
        safety_margin = (
            self.get_parameter("planning.voronoi.safety_margin")
            .get_parameter_value().double_value
        )
        max_edge_len = (
            self.get_parameter("planning.voronoi.max_edge_len")
            .get_parameter_value().double_value
        )

        self.pathPlanner = PathPlanner(
            robot_radius=robot_radius,
            safety_margin=safety_margin,
            max_edge_len=max_edge_len,
        )

        self.frameId = (
            self.get_parameter("planning.topics.frame_id")
            .get_parameter_value().string_value
        )

    def initPubAndSub(self) -> None:
        """
        Initialize publishers and subscribers.
        """
        pathTopic = (
            self.get_parameter("planning.topics.pathTopic")
            .get_parameter_value().string_value
        )
        odometryTopic = (
            self.get_parameter("planning.topics.odometryTopic")
            .get_parameter_value().string_value
        )
        conesTopic = (
            self.get_parameter("planning.topics.conesTopic")
            .get_parameter_value().string_value
        )

        self.publisher = self.create_publisher(Path, pathTopic, 10)
        self.subscriber1 = self.create_subscription(
            MarkerArray, conesTopic, self.receiveFromPerception, 10
        )
        self.subscriber2 = self.create_subscription(
            Odometry, odometryTopic, self.receiveFromLocalization, 10
        )

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        """
        Receives cone data from perception as a MarkerArray and converts it
        to the Voronoi planner's expected format: list of (x, y, color) tuples.

        Args:
            msg (MarkerArray): The cone markers received from perception.
        """
        self.cone_data = []

        for marker in msg.markers:
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            x, y = marker.pose.position.x, marker.pose.position.y

            # Skip white markers
            if r > 0.95 and g > 0.95 and b > 0.95:
                continue

            if g > 0.8:  # Yellow cone
                self.cone_data.append((x, y, 'y'))
            elif b > 0.8 and g < 0.4 and r < 0.4:  # Blue cone
                self.cone_data.append((x, y, 'b'))
            elif marker.ns == "Large Orange Cone":
                # Treat large orange cones as yellow for Voronoi boundary
                self.cone_data.append((x, y, 'y'))
            else:
                # Unknown cones are skipped since Voronoi needs 'y' or 'b'
                continue

        self.sendToControl()

    def receiveFromLocalization(self, msg: Odometry) -> None:
        """
        Receives odometry data from localization.

        Args:
            msg (Odometry): The odometry data from SLAM.
        """
        pose = msg.pose.pose
        orientationQ = pose.orientation
        self.carPosition = np.array([pose.position.x, pose.position.y])

        orientationList = [orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w]
        (_, _, yaw) = euler_from_quaternion(orientationList)
        self.carDirection = yaw

    def sendToControl(self) -> None:
        """
        Runs the Voronoi planner and publishes the resulting path.
        """
        if self.carDirection is None:
            return

        car_data = [(self.carPosition[0], self.carPosition[1], self.carDirection)]
        self.path = self.pathPlanner.execute_cycle(self.cone_data, car_data)

        if self.path:
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = self.frameId

            for point in self.path:
                pose = Pose()
                pose.position.x = float(point[0])
                pose.position.y = float(point[1])

                poseStamped = PoseStamped()
                poseStamped.pose = pose
                poseStamped.header.stamp = timestamp
                poseStamped.header.frame_id = self.frameId

                path_msg.poses.append(poseStamped)

            self.publisher.publish(path_msg)


def main() -> None:
    """
    Initializes ROS2, creates VoronoiPlanningNode, spins, and shuts down.
    """
    rclpy.init()
    node = VoronoiPlanningNode()
    status = StatusPublisher("/status/voronoi_planning_node", node)

    status.starting()
    status.ready()

    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    rate = node.create_rate(100)
    while rclpy.ok():
        rate.sleep()
        status.running()
    node.get_logger().info("ok")


if __name__ == "__main__":
    main()
