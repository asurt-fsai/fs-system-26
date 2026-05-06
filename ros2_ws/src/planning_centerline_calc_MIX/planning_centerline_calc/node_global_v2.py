#!/usr/bin/env python3
"""
Global Path planning node
This node computes a global path using SLAM's global cone map
and the vehicle's global Odometry.
"""

import matplotlib.pyplot as plt
import numpy as np
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Pose, PoseStamped
from tf_transformations import euler_from_quaternion

from src.full_pipeline.full_pipeline import PathPlanner, ParametersState
from src.utils.cone_types import ConeTypes
from src.types_file import FloatArray
from tf_helper.StatusPublisher import StatusPublisher
from tf_helper.TFHelper import TFHelper

class GlobalPlanningNode(Node):
    """
    A class representing a global planning node.

    This node receives the global cone map from SLAM and global Odometry.
    It filters the global cones to only look at those in front of the car,
    and calculates a trajectory strictly in the global space.
    """

    def __init__(self) -> None:
        super().__init__("global_planning_node")
        self.get_logger().info("Global Path Planner V2 instantiated...")

        import os
        import shutil
        self.frames_dir = "node_frames"
        if os.path.exists(self.frames_dir):
            try:
                shutil.rmtree(self.frames_dir)
            except Exception:
                pass
        os.makedirs(self.frames_dir, exist_ok=True)
        self.frame_counter = 0

        self.path: FloatArray = np.zeros((0, 2))
        
        # Cones directly from SLAM global map
        self.cones: list[FloatArray] = [np.zeros((0, 2)) for _ in ConeTypes]
        # Cones filtered to a local window ahead of the car (still in global coords)
        self.filtered_global_cones: list[FloatArray] = [np.zeros((0, 2)) for _ in ConeTypes]
        
        self.carPosition = np.array([0.0, 0.0])
        self.carDirection = 0.0

        # Visualization setup
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Global Path Planning Visualization")
        self.ax.set_xlabel("X (m) [World]")
        self.ax.set_ylabel("Y (m) [World]")
        self.ax.grid(True)
        plt.show(block=False)

        self.publisher: rclpy.publisher.Publisher

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()
        
        self.tfHelper = TFHelper(self)

    def declareParameters(self) -> None:
        """Declare all ROS parameters."""
        self.declare_parameter("planning.sorting.thresholdDirectionalAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.thresholdAbsoluteAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxNNeighbors", rclpy.Parameter.Type.INTEGER)
        self.declare_parameter("planning.sorting.maxDist", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxDistToFirst", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxLength", rclpy.Parameter.Type.INTEGER)

        self.declare_parameter("planning.matching.minTrackWidth", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.maxSearchRange", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.maxSearchAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.matchesShouldBeMonotonic", rclpy.Parameter.Type.BOOL)

        self.declare_parameter("planning.path.maximalDistanceForValidPath", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.path.mpcPathLength", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.path.mpcPredictionHorizon", rclpy.Parameter.Type.INTEGER)

        self.declare_parameter("planning.topics.frame_id", rclpy.Parameter.Type.STRING) # Map frame
        self.declare_parameter("planning.topics.pathTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.odometryTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.conesTopic", rclpy.Parameter.Type.STRING)
        
        # SLAM Cone slice filtering parameters
        self.declare_parameter("planning.slice.radius", 15.0)  # meters
        self.declare_parameter("planning.slice.angle_deg", 180.0)  # degrees (wider for SLAM map)

    def setParameters(self) -> None:
        """Fetch parameters and build Planner state."""
        self.params = ParametersState(
            thresholdDirectionalAngle = np.deg2rad(self.get_parameter("planning.sorting.thresholdDirectionalAngle").get_parameter_value().double_value),
            thresholdAbsoluteAngle = np.deg2rad(self.get_parameter("planning.sorting.thresholdAbsoluteAngle").get_parameter_value().double_value),
            maxNNeighbors = self.get_parameter("planning.sorting.maxNNeighbors").get_parameter_value().integer_value,
            maxDist = self.get_parameter("planning.sorting.maxDist").get_parameter_value().double_value,
            maxDistToFirst = self.get_parameter("planning.sorting.maxDistToFirst").get_parameter_value().double_value,
            maxLength = self.get_parameter("planning.sorting.maxLength").get_parameter_value().integer_value,

            minTrackWidth = self.get_parameter("planning.matching.minTrackWidth").get_parameter_value().double_value,
            maxSearchRange = self.get_parameter("planning.matching.maxSearchRange").get_parameter_value().double_value,
            maxSearchAngle = np.deg2rad(self.get_parameter("planning.matching.maxSearchAngle").get_parameter_value().double_value),
            matchesShouldBeMonotonic = self.get_parameter("planning.matching.matchesShouldBeMonotonic").get_parameter_value().bool_value,

            maximalDistanceForValidPath = self.get_parameter("planning.path.maximalDistanceForValidPath").get_parameter_value().double_value,
            mpcPathLength = self.get_parameter("planning.path.mpcPathLength").get_parameter_value().double_value,
            mpcPredictionHorizon = self.get_parameter("planning.path.mpcPredictionHorizon").get_parameter_value().integer_value
        )
        self.pathPlanner = PathPlanner(self.params)
        self.frameId = self.get_parameter("planning.topics.frame_id").get_parameter_value().string_value
        
        self.slice_radius = self.get_parameter("planning.slice.radius").get_parameter_value().double_value
        self.slice_angle_rad = np.deg2rad(self.get_parameter("planning.slice.angle_deg").get_parameter_value().double_value)

    def initPubAndSub(self) -> None:
        """Initialize publishers and subscribers."""
        pathTopic = self.get_parameter("planning.topics.pathTopic").get_parameter_value().string_value
        conesTopic = self.get_parameter("planning.topics.conesTopic").get_parameter_value().string_value
        odometryTopic = self.get_parameter("planning.topics.odometryTopic").get_parameter_value().string_value
        
        self.publisher = self.create_publisher(Path, pathTopic, 10)
        
        # Subscribe to SLAM Map (MarkerArray)
        self.subscriber1 = self.create_subscription(MarkerArray, conesTopic, self.receiveFromSLAM, 10)
        
        # Subscribe to Global Pose
        self.subscriber2 = self.create_subscription(Odometry, odometryTopic, self.receiveFromLocalization, 10)

    def receiveFromLocalization(self, msg: Odometry) -> None:
        """Continuously update the car's global position and yaw."""
        pose = msg.pose.pose
        self.carPosition = np.array([pose.position.x, pose.position.y])
        
        orientationQ = pose.orientation
        _, _, yaw = euler_from_quaternion([orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w])
        self.carDirection = yaw

    def filter_cones_global(self, cones: list[FloatArray]) -> list[FloatArray]:
        """
        Filter SLAM global map cones to a slice in front of the vehicle.
        Return coordinates still left in the global mapping frame.
        """
        filtered_global_cones = [np.zeros((0, 2)) for _ in ConeTypes]
        half_angle = self.slice_angle_rad / 2

        for i, cone_arr in enumerate(cones):
            if cone_arr.shape[0] == 0:
                continue
                
            # Vector from car to cone in global frame
            rel_vecs = cone_arr - self.carPosition
            
            # Radii
            dists = np.linalg.norm(rel_vecs, axis=1)
            
            # Angle relative to car heading
            # normal arctan2 gives global angle map, subtract carDirection to get relative
            angles = np.arctan2(rel_vecs[:, 1], rel_vecs[:, 0]) - self.carDirection
            
            # Wrap angles to [-pi, pi]
            angles = (angles + np.pi) % (2 * np.pi) - np.pi
            
            mask = (dists <= self.slice_radius) & (np.abs(angles) <= half_angle)
            filtered_global_cones[i] = cone_arr[mask]
            
        return filtered_global_cones

    def receiveFromSLAM(self, msg: MarkerArray) -> None:
        """Process incoming global cone map from SLAM."""
        self.cones = [np.zeros((0, 2)) for _ in ConeTypes]

        for marker in msg.markers:
            x, y = marker.pose.position.x, marker.pose.position.y
            r, g, b = marker.color.r, marker.color.g, marker.color.b

            # Filter white markers (noise)
            if r > 0.95 and g > 0.95 and b > 0.95:
                continue
            elif g > 0.8:
                cone_type = ConeTypes.YELLOW
            elif b > 0.8 and g < 0.4 and r < 0.4:
                cone_type = ConeTypes.BLUE
            elif marker.ns == "Large Orange Cone":
                cone_type = ConeTypes.ORANGE_BIG
            else:
                cone_type = ConeTypes.UNKNOWN
            
            self.cones[cone_type] = np.vstack((self.cones[cone_type], np.array([x, y])))

        # Filter global map so PathPlanner doesn't solve the entire track
        self.filtered_global_cones = self.filter_cones_global(self.cones)
        self.sendToControl()

    def sendToControl(self) -> None:
        """Call global planner and publish out global path points."""
        if self.carDirection is None:
            return

        self.path = self.pathPlanner.calculatePathInGlobalFrame(
            vehiclePosition=self.carPosition,
            vehicleDirection=self.carDirection,
            cones=self.filtered_global_cones
        )
        
        if self.path is not None:
            # Publish path
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = self.frameId

            for dataPoint in self.path:
                pose = Pose()
                pose.position.x = dataPoint[0]
                pose.position.y = dataPoint[1]
                
                poseStamped = PoseStamped()
                poseStamped.pose = pose
                poseStamped.header.stamp = timestamp
                poseStamped.header.frame_id = self.frameId
                path_msg.poses.append(poseStamped)

            self.publisher.publish(path_msg)
            self.visualize()

    def visualize(self) -> None:
        """Plots the global map state."""
        self.ax.clear()
        self.ax.set_title("Global Path Planning Visualization")
        self.ax.set_xlabel("X (m) [World]")
        self.ax.set_ylabel("Y (m) [World]")
        self.ax.grid(True)

        # Plot converted Global Cones
        blue_cones = self.filtered_global_cones[ConeTypes.BLUE]
        yellow_cones = self.filtered_global_cones[ConeTypes.YELLOW]
        if blue_cones.shape[0] > 0:
            self.ax.plot(blue_cones[:, 0], blue_cones[:, 1], 'bo', label='SLAM Blue Cones', markersize=3)
        if yellow_cones.shape[0] > 0:
            self.ax.plot(yellow_cones[:, 0], yellow_cones[:, 1], 'yo', label='SLAM Yellow Cones', markersize=3)

        # Plot Global Path
        if self.path is not None and self.path.shape[0] > 0:
            self.ax.plot(self.path[:, 0], self.path[:, 1], 'r-', label='Global Path')

        # Plot Global Car Pose
        self.ax.plot(self.carPosition[0], self.carPosition[1], 'ko', label='Car Position')
        # Tiny arrow to denote direction
        dx = np.cos(self.carDirection) * 0.5
        dy = np.sin(self.carDirection) * 0.5
        self.ax.arrow(self.carPosition[0], self.carPosition[1], dx, dy, head_width=0.4, head_length=0.4, fc='k', ec='k')

        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

        import os
        self.fig.savefig(os.path.join(self.frames_dir, f"frame_{self.frame_counter:04d}.png"))
        self.frame_counter += 1

def main() -> None:
    rclpy.init()
    node = GlobalPlanningNode()
    status = StatusPublisher("/status/planning_node", node)
    status.starting()
    status.ready()

    rate = node.create_rate(100)
    while rclpy.ok():
        rclpy.spin_once(node)
        status.running()
        rate.sleep()
    node.get_logger().info("Shutting down Global Planning Node...")

if __name__ == "__main__":
    main()
