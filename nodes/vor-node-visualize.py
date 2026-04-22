#!/usr/bin/env python3
"""
Voronoi Path Planning ROS2 Node
This node is responsible for starting the Voronoi-based path planning module.
This is the current node i am using.
"""

import threading
import time
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import Pose, PoseStamped
import numpy as np
from tf_transformations import euler_from_quaternion
from tf_helper.StatusPublisher import StatusPublisher

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    plt = None
    MATPLOTLIB_AVAILABLE = False

from planning_voronoi.modules.planner import PathPlanner


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
        self.carPosition = None
        self.carDirection = None
        self.localization_ready = False
        self.last_localization_time = None
        self._warned_no_localization = False
        self._warned_stale_localization = False

        self.state_lock = threading.Lock()
        self.visualization_enabled = False
        self.plot_period_sec = 0.05
        self.axis_margin_m = 2.0
        self.follow_car_view = True
        self.follow_front_m = 18.0
        self.follow_back_m = 4.0
        self.follow_half_width_m = 6.0
        self._last_axis_limits = None
        self.follow_axis_smoothing_alpha = 0.25
        self._last_plot_time = 0.0
        self.fig = None
        self.ax = None

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()

    def declareParameters(self) -> None:
        """
        Declare the ROS2 parameters for the Voronoi planning node.
        Robot_radius =0.7
        Safety_margin=0.4
        max_edge_len=8.0
        """
        self.declare_parameter("planning.voronoi.robot_radius", 0.7)  # Vehicle collision radius.
        self.declare_parameter("planning.voronoi.safety_margin", 0.4)  # Extra clearance added around cones to keep path conservative.
        self.declare_parameter("planning.voronoi.max_edge_len", 8.0)  # Max Voronoi graph edge length considered for path search.
        self.declare_parameter("planning.voronoi.max_odom_age_sec", 0.5)  # Reject planning if latest odometry is older than this threshold (seconds).

        self.declare_parameter("planning.topics.frame_id", "map")  # Frame ID.
        self.declare_parameter("planning.topics.pathTopic", "/planning/path")
        self.declare_parameter("planning.topics.odometryTopic", "/odometry")
        self.declare_parameter("planning.topics.conesTopic", "/cone_map")

        self.declare_parameter("planning.visualization.enable", True)  # Enable/disable matplotlib live window.
        self.declare_parameter("planning.visualization.refresh_hz", 20.0)  # Plot redraw rate limit to reduce GUI/CPU load.
        self.declare_parameter("planning.visualization.axis_margin_m", 2.0)  # Minimum plot border around cones/car/path in meters.
        self.declare_parameter("planning.visualization.follow_car_view", True)  # Keep the camera centered on the car region instead of global fit.
        self.declare_parameter("planning.visualization.follow_front_m", 18.0)  # How far ahead of the car to show (meters).
        self.declare_parameter("planning.visualization.follow_back_m", 4.0)  # How far behind the car to keep visible (meters).
        self.declare_parameter("planning.visualization.follow_half_width_m", 6.0)  # Half-width of side view around car heading (meters).
        self.declare_parameter("planning.visualization.follow_axis_smoothing_alpha", 0.25)  # Smoothing factor (0-1) for camera motion.

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
        self.max_odom_age_sec = (
            self.get_parameter("planning.voronoi.max_odom_age_sec")
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

        self.visualization_enabled = (
            self.get_parameter("planning.visualization.enable")
            .get_parameter_value().bool_value
        )
        refresh_hz = (
            self.get_parameter("planning.visualization.refresh_hz")
            .get_parameter_value().double_value
        )
        self.axis_margin_m = (
            self.get_parameter("planning.visualization.axis_margin_m")
            .get_parameter_value().double_value
        )
        self.follow_car_view = (
            self.get_parameter("planning.visualization.follow_car_view")
            .get_parameter_value().bool_value
        )
        self.follow_front_m = (
            self.get_parameter("planning.visualization.follow_front_m")
            .get_parameter_value().double_value
        )
        self.follow_back_m = (
            self.get_parameter("planning.visualization.follow_back_m")
            .get_parameter_value().double_value
        )
        self.follow_half_width_m = (
            self.get_parameter("planning.visualization.follow_half_width_m")
            .get_parameter_value().double_value
        )
        self.follow_axis_smoothing_alpha = (
            self.get_parameter("planning.visualization.follow_axis_smoothing_alpha")
            .get_parameter_value().double_value
        )
        self.follow_axis_smoothing_alpha = max(0.0, min(1.0, self.follow_axis_smoothing_alpha))
        self.plot_period_sec = 1.0 / max(1.0, refresh_hz)  # Converts refresh_hz to redraw period for throttled plotting.

        if self.visualization_enabled and not MATPLOTLIB_AVAILABLE:
            self.get_logger().warn(
                "Visualization requested, but matplotlib is not available. Disabling plot window."
            )
            self.visualization_enabled = False
        elif self.visualization_enabled:
            self.initialize_plot()

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

    def initialize_plot(self) -> None:
        """Created an interactive matplotlib window."""
        try:
            plt.ion()
            self.fig, self.ax = plt.subplots(figsize=(10, 8))
            self.fig.suptitle("Voronoi Path Planning Visualization")
            self.ax.set_aspect("equal", "box")
            self.ax.set_xlabel("X (m)")
            self.ax.set_ylabel("Y (m)")
            self.ax.grid(True, alpha=0.3)
            self.fig.tight_layout()
            self.fig.show()
            plt.pause(0.001)
            self.get_logger().info("Visualization window initialized.")
        except Exception as exc:
            self.get_logger().warn(f"Failed to initialize visualization window: {exc}")
            self.visualization_enabled = False

    # def _manual_view_active(self) -> bool:
    #     """Return True when the Matplotlib toolbar is in zoom/pan interaction mode."""
    #     if self.fig is None:
    #         return False
    #
    #     manager = getattr(self.fig.canvas, "manager", None)
    #     toolbar = getattr(manager, "toolbar", None)
    #     mode = getattr(toolbar, "mode", "")
    #     if mode:
    #         return True
    #
    #     toolmanager = getattr(manager, "toolmanager", None)
    #     if toolmanager is not None:
    #         active_tool = getattr(toolmanager, "active_toggle", None)
    #         if active_tool:
    #             return True
    #
    #     return False

    def process_visualization(self) -> None:
        if not self.visualization_enabled or self.fig is None or self.ax is None:
            return

        now = time.monotonic()
        if now - self._last_plot_time < self.plot_period_sec:
            return
        self._last_plot_time = now

        # manual_view = self._manual_view_active()
        # if manual_view:
        #     preserved_xlim = self.ax.get_xlim()
        #     preserved_ylim = self.ax.get_ylim()
        # else:
        #     preserved_xlim = None
        #     preserved_ylim = None

        with self.state_lock:
            cones = list(self.cone_data)
            path = list(self.path)
            car_pos = None if self.carPosition is None else np.array(self.carPosition, copy=True)
            car_yaw = self.carDirection

        self.ax.clear()
        self.ax.set_aspect("equal", "box")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.grid(True, alpha=0.3) # alpha controls grid line transparency

        yellow_cones = [(x, y) for x, y, c in cones if c == "y"]
        blue_cones = [(x, y) for x, y, c in cones if c == "b"]

        if yellow_cones:
            self.ax.scatter(
                [c[0] for c in yellow_cones],
                [c[1] for c in yellow_cones],
                c="yellow",
                edgecolors="orange",
                s=70, # controls marker size in scatter
                label="Yellow Cones",
            )

        if blue_cones:
            self.ax.scatter(
                [c[0] for c in blue_cones],
                [c[1] for c in blue_cones],
                c="blue",
                edgecolors="navy",
                s=70,
                label="Blue Cones",
            )

        all_x = [c[0] for c in cones]
        all_y = [c[1] for c in cones]

        if car_pos is not None:
            self.ax.scatter(car_pos[0], car_pos[1], c="red", marker="^", s=120, label="Car")
            if car_yaw is not None:
                self.ax.arrow(
                    car_pos[0],
                    car_pos[1],
                    np.cos(car_yaw),
                    np.sin(car_yaw),
                    head_width=0.25,
                    head_length=0.3,
                    fc="red",
                    ec="red",
                )
            all_x.append(float(car_pos[0]))
            all_y.append(float(car_pos[1]))

        if path:
            path_x = [float(p[0]) for p in path]
            path_y = [float(p[1]) for p in path]
            self.ax.plot(path_x, path_y, "g-", linewidth=2.0, label="Planned Path")
            all_x.extend(path_x)
            all_y.extend(path_y)

        # if manual_view and preserved_xlim is not None and preserved_ylim is not None:
        #     # Keep the user's zoom/pan view active while still refreshing the plotted data.
        #     self.ax.set_xlim(preserved_xlim)
        #     self.ax.set_ylim(preserved_ylim)
        # elif (
        #     self.follow_car_view
        #     and car_pos is not None
        #     and car_yaw is not None
        # ):
        if self.follow_car_view and car_pos is not None and car_yaw is not None:
            forward = np.array([np.cos(car_yaw), np.sin(car_yaw)])
            left = np.array([-np.sin(car_yaw), np.cos(car_yaw)])

            # Camera center is biased forward to show more of near-term trajectory.
            center = car_pos + forward * ((self.follow_front_m - self.follow_back_m) * 0.5)
            half_x = max(self.follow_half_width_m, 1.0)
            half_y = max((self.follow_front_m + self.follow_back_m) * 0.5, 1.0)

            corners = []
            for sx in (-half_x, half_x):
                for sy in (-half_y, half_y):
                    p = center + left * sx + forward * sy
                    corners.append(p)

            x_min = min(float(p[0]) for p in corners)
            x_max = max(float(p[0]) for p in corners)
            y_min = min(float(p[1]) for p in corners)
            y_max = max(float(p[1]) for p in corners)

            target_limits = (x_min, x_max, y_min, y_max)
            if self._last_axis_limits is None or self.follow_axis_smoothing_alpha <= 0.0:
                smooth_limits = target_limits
            else:
                a = self.follow_axis_smoothing_alpha
                smooth_limits = tuple(
                    (1.0 - a) * prev + a * target
                    for prev, target in zip(self._last_axis_limits, target_limits)
                )
            self._last_axis_limits = smooth_limits

            self.ax.set_xlim(smooth_limits[0], smooth_limits[1])
            self.ax.set_ylim(smooth_limits[2], smooth_limits[3])
        elif all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_margin = max((x_max - x_min) * 0.1, self.axis_margin_m)
            y_margin = max((y_max - y_min) * 0.1, self.axis_margin_m)
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)

        handles, labels = self.ax.get_legend_handles_labels()
        if handles and labels:
            self.ax.legend(loc="upper right")

        self.fig.canvas.draw_idle()
        plt.pause(0.001)

    def close_visualization(self) -> None:
        """Close matplotlib resources during shutdown."""
        if self.fig is not None and MATPLOTLIB_AVAILABLE:
            try:
                plt.close(self.fig)
            except Exception:
                pass

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        """
        Receives cone data from perception as a MarkerArray and converts it
        to the Voronoi planner's expected format: list of (x, y, color) tuples.

        Args:
            msg (MarkerArray): The cone markers received from perception.
        """
        cone_data = []

        for marker in msg.markers:
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            x, y = marker.pose.position.x, marker.pose.position.y

            # Skip white markers
            if r > 0.95 and g > 0.95 and b > 0.95:
                continue

            if g > 0.8:  # Yellow cone
                cone_data.append((x, y, 'y'))
            elif b > 0.8 and g < 0.4 and r < 0.4:  # Blue cone
                cone_data.append((x, y, 'b'))
            elif marker.ns == "Large Orange Cone":
                # Treat large orange cones as yellow for Voronoi boundary
                cone_data.append((x, y, 'y'))
            else:
                # Unknown cones are skipped since Voronoi needs 'y' or 'b'
                continue

        with self.state_lock:
            self.cone_data = cone_data

        self.sendToControl()

    def receiveFromLocalization(self, msg: Odometry) -> None:
        """
        Receives odometry data from localization.

        Args:
            msg (Odometry): The odometry data from SLAM.
        """
        pose = msg.pose.pose
        orientationQ = pose.orientation
        car_position = np.array([pose.position.x, pose.position.y])

        orientationList = [orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w]
        (_, _, yaw) = euler_from_quaternion(orientationList)

        with self.state_lock:
            self.carPosition = car_position
            self.carDirection = yaw
            self.localization_ready = True
            self.last_localization_time = self.get_clock().now()
            self._warned_no_localization = False

    def sendToControl(self) -> None:
        """
        Runs the Voronoi planner and publishes the resulting path.
        """
        with self.state_lock:
            localization_ready = self.localization_ready
            car_position = None if self.carPosition is None else np.array(self.carPosition, copy=True)
            car_direction = self.carDirection
            last_localization_time = self.last_localization_time
            cone_data = list(self.cone_data)

        if not localization_ready or car_position is None or car_direction is None:
            if not self._warned_no_localization:
                self.get_logger().warn("Waiting for odometry before planning path.")
                self._warned_no_localization = True
            return

        odom_age_sec = (
            (self.get_clock().now() - last_localization_time).nanoseconds / 1e9
            if last_localization_time is not None
            else float("inf")
        )
        if odom_age_sec > self.max_odom_age_sec:
            if not self._warned_stale_localization:
                self.get_logger().warn(
                    f"Odometry is stale ({odom_age_sec:.2f}s old). Skipping path publish."
                )
                self._warned_stale_localization = True
            return
        self._warned_stale_localization = False

        car_data = [(car_position[0], car_position[1], car_direction)]
        path = self.pathPlanner.execute_cycle(cone_data, car_data)

        with self.state_lock:
            self.path = path if path else []

        if path:
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = self.frameId

            for point in path:
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

    try:
        while rclpy.ok():
            rate.sleep()
            node.process_visualization()
            status.running()
    finally:
        node.close_visualization()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

