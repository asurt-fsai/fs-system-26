#!/usr/bin/env python3
"""
Path planning node
This node is responsible for starting the path planning module
"""

import threading
from typing import Any, List
import math

from matplotlib.ticker import MultipleLocator
import rclpy
from rclpy.node import Node
from asurt_msgs.msg import LandmarkArray,Landmark
from visualization_msgs.msg import MarkerArray, Marker
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import Pose, PoseStamped
import numpy as np
from tf_transformations import euler_from_quaternion
from tf_helper.StatusPublisher import StatusPublisher
from tf_helper.TFHelper import TFHelper

from src.full_pipeline.full_pipeline import PathPlanner, ParametersState
from src.utils.cone_types import ConeTypes
from src.types_file import FloatArray
import matplotlib.pyplot as plt
import csv

class PlanningNode(Node): # pylint: disable=too-many-instance-attributes
    """
    A class representing a planning node.

    This node is responsible for receiving data from perception and localization,
    calculating a path based on the received data, and sending the path to control.

    Attributes:
        path (list): The calculated path.
        cones (list): The positions of cones detected by perception.
        carPosition (list): The position of the car.
        carDirection (list): The direction of the car.
        subscriber1 (Subscriber): The subscriber for receiving data from perception.
        subscriber2 (Subscriber): The subscriber for receiving data from localization.
        publisher (Publisher): The publisher for sending the calculated path.

    Methods:
        receive_from_perception: Receives data from perception.
        receive_from_localization: Receives data from localization.
        send_to_control: Sends the calculated path to control.
    """

    def __init__(self) -> None:
        super().__init__("planning_node")
        self.get_logger().info("Path Planner GLOBAL instantiated...")
        self.path: FloatArray = np.zeros((0, 2))
        self.cones: List[FloatArray] = [np.zeros((0, 2)) for _ in ConeTypes]
        self.carPosition = np.array([0, 0])
        self.carDirection = np.float64(0.0)

        self.fig, self.ax = plt.subplots()
        self.blue_scatter = self.ax.scatter([], [], c='blue')
        self.yellow_scatter = self.ax.scatter([], [], c='yellow')
        self.path_line, = self.ax.plot([], [], 'r-')  # red line
        self.car_pos_plot = self.ax.plot([], [], 'ko')[0]  # car position as black dot

        self.ax.set_title("Path Planning Visualization")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.grid(True)
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:            # only if there’s at least one non‑underscore label
            self.ax.legend()
        #self.ax.legend()
        plt.show(block=False)


        self.publisher: rclpy.publisher.Publisher

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()
        


        self.tfHelper = TFHelper(self)

    def declareParameters(self) -> None:
        """
        Declare the parameters for the planning node.
        """
        self.declare_parameter(
            "planning.sorting.thresholdDirectionalAngle", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.sorting.thresholdAbsoluteAngle", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.sorting.maxNNeighbors", rclpy.Parameter.Type.INTEGER
            )
        self.declare_parameter(
            "planning.sorting.maxDist", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.sorting.maxDistToFirst", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.sorting.maxLength", rclpy.Parameter.Type.INTEGER
            )

        self.declare_parameter(
            "planning.matching.minTrackWidth", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.matching.maxSearchRange", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.matching.maxSearchAngle", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.matching.matchesShouldBeMonotonic", rclpy.Parameter.Type.BOOL
            )

        self.declare_parameter(
            "planning.path.maximalDistanceForValidPath", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.path.mpcPathLength", rclpy.Parameter.Type.DOUBLE
            )
        self.declare_parameter(
            "planning.path.mpcPredictionHorizon", rclpy.Parameter.Type.INTEGER
            )

        self.declare_parameter("planning.topics.frame_id", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.pathTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.odometryTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.conesTopic", rclpy.Parameter.Type.STRING)
        
        self.declare_parameter("planning.slice.radius", 8.0)  # meters
        self.declare_parameter("planning.slice.angle_deg", 90.0)  # degrees

    def setParameters(self) -> None:
        """
        Get parameters from the parameter server and set them to their respective varibles
        """
        thresholdDirectionalAngle = (
            np.deg2rad(
                self.get_parameter(
                    "planning.sorting.thresholdDirectionalAngle"
                    ).get_parameter_value().double_value
                )
            )
        thresholdAbsoluteAngle = (
            np.deg2rad(
                self.get_parameter(
                    "planning.sorting.thresholdAbsoluteAngle"
                    ).get_parameter_value().double_value
                )
            )
        maxNNeighbors = (
            self.get_parameter(
                "planning.sorting.maxNNeighbors"
                ).get_parameter_value().integer_value
            )
        maxDist = (
            self.get_parameter(
                "planning.sorting.maxDist"
                ).get_parameter_value().double_value
            )
        maxDistToFirst = (
            self.get_parameter(
                "planning.sorting.maxDistToFirst"
                ).get_parameter_value().double_value
            )
        maxLength = (
            self.get_parameter(
                "planning.sorting.maxLength"
                ).get_parameter_value().integer_value
            )

        minTrackWidth = (
            self.get_parameter(
                "planning.matching.minTrackWidth"
                ).get_parameter_value().double_value
            )
        maxSearchRange = (
            self.get_parameter(
                "planning.matching.maxSearchRange"
                ).get_parameter_value().double_value
            )
        maxSearchAngle = (
                np.deg2rad(
                    self.get_parameter(
                        "planning.matching.maxSearchAngle"
                        ).get_parameter_value().double_value
                    )
            )
        matchesShouldBeMonotonic = (
            self.get_parameter(
                "planning.matching.matchesShouldBeMonotonic"
                ).get_parameter_value().bool_value
            )

        maximalDistanceForValidPath = (
            self.get_parameter(
                "planning.path.maximalDistanceForValidPath"
                ).get_parameter_value().double_value
            )
        mpcPathLength = (
            self.get_parameter(
                "planning.path.mpcPathLength"
                ).get_parameter_value().double_value
            )
        mpcPredictionHorizon = (
            self.get_parameter(
                "planning.path.mpcPredictionHorizon"
                ).get_parameter_value().integer_value
            )
        
        self.slice_radius = self.get_parameter("planning.slice.radius").get_parameter_value().double_value
        self.slice_angle_deg = self.get_parameter("planning.slice.angle_deg").get_parameter_value().double_value
        self.slice_angle_rad = np.deg2rad(self.slice_angle_deg)

        self.params = ParametersState(
            thresholdDirectionalAngle = thresholdDirectionalAngle,
            thresholdAbsoluteAngle = thresholdAbsoluteAngle,
            maxNNeighbors = maxNNeighbors,
            maxDist = maxDist,
            maxDistToFirst = maxDistToFirst,
            maxLength = maxLength,

            minTrackWidth = minTrackWidth,
            maxSearchRange = maxSearchRange,
            maxSearchAngle = maxSearchAngle,
            matchesShouldBeMonotonic = matchesShouldBeMonotonic,

            maximalDistanceForValidPath = maximalDistanceForValidPath,
            mpcPathLength = mpcPathLength,
            mpcPredictionHorizon = mpcPredictionHorizon
        )

        self.pathPlanner = PathPlanner(self.params)

        self.frameId = (
            self.get_parameter("planning.topics.frame_id").get_parameter_value().string_value
        )

    def initPubAndSub(self) -> None:
        """
        Initialize Publishers and subscribers for planning node

        Parameters
        ----------

        pathTopic: str
            The topic to publish the path
        
        odometryTopic: str
            The topic to subscribe to the odometry information comming from SLAM

        conesTopic: str
            The topic to subscribe to the cones information comming from SLAM
        """
        pathTopic = (
            self.get_parameter("planning.topics.pathTopic").get_parameter_value().string_value
        )
        odometryTopic = (
            self.get_parameter("planning.topics.odometryTopic").get_parameter_value().string_value
        )
        conesTopic = (
            self.get_parameter("planning.topics.conesTopic").get_parameter_value().string_value
        )
        self.publisher = self.create_publisher(Path, pathTopic, 10)
        self.subscriber1 = self.create_subscription(
            MarkerArray, conesTopic, self.receiveFromPerception, 10
        )
        self.subscriber2 = self.create_subscription(
            Odometry, odometryTopic, self.receiveFromLocalization, 10
        )

    def filter_cones_global(self, cones, car_pos, car_yaw):
        """
        Filter cones within a pizza slice in front of the car (all in global frame).
        Args:
            cones: List of np.array of shape (N,2) for each cone type (global frame)
            car_pos: np.array([x, y]) (global)
            car_yaw: float (global)
        Returns:
            filtered_global_cones: List of np.array of shape (M,2) for each cone type (global frame)
        """
        filtered_global_cones = [np.zeros((0, 2)) for _ in ConeTypes]
        half_angle = self.slice_angle_rad / 2

        for cone_type, cone_arr in enumerate(cones):
            if cone_arr.shape[0] == 0:
                continue
            # Vector from car to cone in global frame
            rel = cone_arr - car_pos  # shape (N,2)
            # Angle of each cone relative to car heading (in global frame)
            dists = np.linalg.norm(rel, axis=1)
            angles = np.arctan2(rel[:, 1], rel[:, 0]) - car_yaw
            # Filter by radius and angle
            mask = (dists <= self.slice_radius) & (np.abs(angles) <= half_angle)
            filtered_global_cones[cone_type] = cone_arr[mask]
        return filtered_global_cones

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        """
        Receives data from perception in the form of a MarkerArray.

        Args:
            msg (MarkerArray): The data received from perception.
        """
        # Transform the received message if necessary
        #msg = self.tfHelper.transformMsg(msg, self.frameId)
        #self.get_logger().info("Received MarkerArray")
        self.cones = [np.zeros((0, 2)) for _ in ConeTypes]
        
        # total = len(msg.markers)
        # msg.markers = msg.markers[:total//2]
             
        for marker in msg.markers:
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            x, y = marker.pose.position.x, marker.pose.position.y

            # Skip white markers (possibly artifacts or ignored markers)
            if r > 0.95 and g > 0.95 and b > 0.95:
                #self.get_logger().info("\nSkipping white marker...\n")
                continue
            
            # Determine cone type based on color
            elif g > 0.8:  # Yellow Cone
                # self.get_logger().info("\Yellow Cone\n")
                cone_type = ConeTypes.YELLOW
            elif b > 0.8 and g < 0.4 and r < 0.4:  # Blue Cone
                cone_type = ConeTypes.BLUE
                # self.get_logger().info("\Blue Cone\n")
            elif marker.ns == "Large Orange Cone":  # Large Orange Cone
                cone_type = ConeTypes.ORANGE_BIG
            else:  # Unknown cone type
                cone_type = ConeTypes.UNKNOWN
                # self.get_logger().info("\nDakhalt Fel Unknown Zeft\n")

            # Append position to the corresponding cone type
            self.cones[cone_type] = np.vstack((self.cones[cone_type], np.array([x, y])))

            # Append to global list
            self.all_cones_xy.append((x, y, cone_type))

        # === NEW: Filter cones in global frame ===
        car_pos = self.carPosition.copy()
        car_yaw = self.carDirection
        filtered_global_cones = self.filter_cones_global(self.cones, car_pos, car_yaw)
        self.filtered_global_cones = filtered_global_cones  # Save for plotting if needed
        self.sendToControl()
        
    def receiveFromLocalization(self, msg: Odometry) -> None:
        """
        Receives data from localization.

        Args:
            msg (Odometry): The data received from localization.
        """
        # get car_position, car_direction
        pose = msg.pose.pose
        orientationQ = pose.orientation
        self.carPosition = np.array([pose.position.x, pose.position.y])
        #self.carPosition = np.array([0,0])

        orientationList = [orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w]
        (_, _, yaw) = euler_from_quaternion(orientationList)
        self.carDirection = yaw
        #self.carDirection = 1.57



    def sendToControl(self) -> None:
        """
        Sends the calculated path to control.
        """
        if self.carDirection is None:
            return

        # Call planner with car's global position, heading, and filtered cones (all in global frame)
        path_global = self.pathPlanner.calculatePathInGlobalFrame(
            vehiclePosition=self.carPosition,
            vehicleDirection=self.carDirection,
            cones=self.filtered_global_cones
        )
        self.path = None
        if path_global is not None:
            self.path = path_global

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

            # === Plotting (filtered cones and path in global frame) ===
            self.ax.clear()
            self.ax.set_title("Path Planning Visualization")
            self.ax.set_xlabel("X (m)")
            self.ax.set_ylabel("Y (m)")
            self.ax.grid(True)
            handles, labels = self.ax.get_legend_handles_labels()
            if labels:
                self.ax.legend()

            # Plot all cones (global)
            blue_cones = self.cones[ConeTypes.BLUE]
            yellow_cones = self.cones[ConeTypes.YELLOW]
            if blue_cones.shape[0] > 0:
                self.ax.plot(blue_cones[:, 0], blue_cones[:, 1], 'bo', markersize=3)
            if yellow_cones.shape[0] > 0:
                self.ax.plot(yellow_cones[:, 0], yellow_cones[:, 1], 'yo', markersize=3)

            # Plot filtered cones (global)
            for cone_type, color, label in [
                (ConeTypes.BLUE, 'b*', 'Filtered Blue'),
                (ConeTypes.YELLOW, 'y*', 'Filtered Yellow')
            ]:
                global_cones = self.filtered_global_cones[cone_type]
                if global_cones.shape[0] > 0:
                    self.ax.plot(global_cones[:, 0], global_cones[:, 1], color, label=label, markersize=6)

            # Plot path as red line
            if self.path is not None and self.path.shape[0] > 0:
                self.ax.plot(self.path[:, 0], self.path[:, 1], 'r-')

            # Plot car position as black dot
            self.ax.plot(self.carPosition[0], self.carPosition[1], 'ko')

            if self.pathPlanner.cornerCaseFlag:
                case_label = "Corner Case"
            elif self.pathPlanner.normalCaseFlag:
                case_label = "Normal Case"
            else:
                case_label = "Unknown Case"

            # Add a dummy plot for the legend
            self.ax.plot([], [], ' ', label=f"Case: {case_label}")

            # Update legend (rebuild to include new label)
            handles, labels = self.ax.get_legend_handles_labels()
            self.ax.legend(handles, labels)

            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(0.001)

    ######## Additional functions for debugging ########

    def declare_cone_map(self):
        self.all_cones_xy = []  # x, y, cone_type


    def save_cone_map_to_csv(self, path="cone_map.csv"):
        with open(path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["x", "y", "cone_type"])
            for x, y, cone_type in self.all_cones_xy:
                writer.writerow([x, y, cone_type])
        self.get_logger().info(f"Saved full cone map to: {path}")




def main() -> None:
    """
    Initializes ROS, creates PlanningNode, spins, & shuts down.
    """
    rclpy.init()
    node = PlanningNode()
    status = StatusPublisher("/status/planning_node", node)

    status.starting()
    node.declare_cone_map()

    # Publish heartbeat to show the module is ready
    status.ready()

    # Main loop
    # Spin in a seperate thread
    # thread = threading.Thread(target=rclpy.spin, args=(node, ), daemon=True)
    # thread.start()
    rclpy.spin(node)
    rate = node.create_rate(100)
    while rclpy.ok():
        rate.sleep()
        # Publish heartbeat to show the module is running
        status.running()
    node.get_logger().info("ok")


if __name__ == "__main__":
    main()
