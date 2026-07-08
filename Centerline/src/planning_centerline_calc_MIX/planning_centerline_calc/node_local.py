#!/usr/bin/env python3
"""
Local Path planning node
This node computes a local path using only local cone detections.
It does not subscribe to or require Odometry.
"""
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray, Marker
from nav_msgs.msg import Path
#from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Pose, PoseStamped
import math

from src.full_pipeline.full_pipeline import PathPlanner, ParametersState
from src.utils.cone_types import ConeTypes
from src.types_file import FloatArray
from tf_helper.StatusPublisher import StatusPublisher
from tf_helper.TFHelper import TFHelper

class LocalPlanningNode(Node):
    """
    A class representing a local planning node.

    This node receives data purely from perception in the local frame,
    calculates a path based on these cones, and sends the local path to control.
    """

    def __init__(self) -> None:
        super().__init__("local_planning_node")
        self.get_logger().info("Local Path Planner instantiated...")
        self.status = StatusPublisher("/status/planning_node", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()
        
        
        
        
        
        self.path: FloatArray = np.zeros((0, 2))
        self.cones: list[FloatArray] = [np.zeros((0, 2)) for _ in ConeTypes]
        
        # Vehicle is always at the origin facing X-axis in the local frame
        self.carPosition = np.array([0.0, 0.0])
        self.carDirection = 0.0

        # Visualization setup
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Local Path Planning Visualization")
        self.ax.set_xlabel("X (m) [Forward]")
        self.ax.set_ylabel("Y (m) [Left]")
        self.ax.grid(True)
        plt.show(block=False)

        self.publisher: rclpy.publisher.Publisher

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()
        
        self.tfHelper = TFHelper(self)

        # --- Lap Counting & Failsafe ---
        self.lap_count = 0
        self.target_laps = 1
        self.mission_finished = False
        self.last_lap_time = self.get_clock().now()
        self.lap_cooldown_seconds = 15.0  # Adjust based on your expected minimum lap time

    def declareParameters(self) -> None:
        """Declare the parameters for the planning node."""
        # Sorting parameters
        self.declare_parameter("planning.sorting.thresholdDirectionalAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.thresholdAbsoluteAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxNNeighbors", rclpy.Parameter.Type.INTEGER)
        self.declare_parameter("planning.sorting.maxDist", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxDistToFirst", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.sorting.maxLength", rclpy.Parameter.Type.INTEGER)

        # Matching parameters
        self.declare_parameter("planning.matching.minTrackWidth", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.maxSearchRange", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.maxSearchAngle", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.matching.matchesShouldBeMonotonic", rclpy.Parameter.Type.BOOL)

        # Path parameteres
        self.declare_parameter("planning.path.maximalDistanceForValidPath", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.path.mpcPathLength", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("planning.path.mpcPredictionHorizon", rclpy.Parameter.Type.INTEGER)

        # ROS topics metadata
        self.declare_parameter("planning.topics.frame_id", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.pathTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("planning.topics.conesTopic", rclpy.Parameter.Type.STRING)
        
        # View area limit
        self.declare_parameter("planning.slice.radius", 15.0)  # meters
        self.declare_parameter("planning.slice.angle_deg", 90.0)  # degrees

    def setParameters(self) -> None:
        """Retrieve parameters from the server and configure the Path Planner."""
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
        
        #self.publisher = self.create_publisher(Path, pathTopic, 10)
        #self.subscriber = self.create_subscription(MarkerArray, conesTopic, self.receiveFromPerception, 10)
        #pathTopic = "/path"
        #conesTopic = "/carmaker/ObjectList"  # Hardcoded CarMaker topic
        
        self.publisher = self.create_publisher(Path, pathTopic, 10)
        self.subscriber = self.create_subscription(MarkerArray, conesTopic, self.receiveFromPerception, 10)

    def filter_local_cones(self) -> None:
        """Keep only cones within the local view slice and remove anomalies."""
        half_angle = self.slice_angle_rad / 2
        for i in range(len(self.cones)):
            if self.cones[i].shape[0] == 0:
                continue
                
            # 1. Remove duplicate cones to prevent [0,0] vectors between identical points
            self.cones[i] = np.unique(self.cones[i], axis=0)

            xs = self.cones[i][:, 0]
            ys = self.cones[i][:, 1]
            dists = np.sqrt(xs**2 + ys**2)
            angles = np.arctan2(ys, xs)
            
            # 2. Add `dists > 0.05` to ignore phantom cones at the car's exact origin
            mask = (dists > 0.05) & (dists <= self.slice_radius) & (np.abs(angles) <= half_angle)
            self.get_logger().info(f"Cones remaining after filter: {sum(len(c) for c in self.cones)}")
            filtered_cones = self.cones[i][mask]
            
            # 3. Sort cones by distance from the car! np.unique scrambles the order.
            if len(filtered_cones) > 0:
                dists_filtered = np.linalg.norm(filtered_cones, axis=1)
                sort_indices = np.argsort(dists_filtered)
                self.cones[i] = filtered_cones[sort_indices]
            else:
                self.cones[i] = np.zeros((0, 2))

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        """Process incoming local cones from perception."""
        try:
            # Transform the received message if necessary
            # We MUST transform otherwise coordinates are stuck in the Object Sensor Frame!
            msg = self.tfHelper.transformMsg(msg, self.frameId)
            
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
                elif "Orange" in marker.ns or "orange" in marker.ns:  # Large Orange Cone
                    cone_type = ConeTypes.ORANGE_BIG
                else:  # Unknown cone type
                    cone_type = ConeTypes.UNKNOWN
                # self.get_logger().info("\nDakhalt Fel Unknown Zeft\n")

                # Append position to the corresponding cone type
                self.cones[cone_type] = np.vstack((self.cones[cone_type], np.array([x, y])))

            self.filter_local_cones()
            self.sendToControl()

        except Exception as e:
            self.get_logger().error(f"Error in receiveFromPerception: {e}")

    def updateLapCount(self) -> None:
        """Checks if a lap has been completed and updates the lap count."""
        if self.mission_finished:
            return
        
        orange_cones = self.cones[ConeTypes.ORANGE_BIG]
        
        if len(orange_cones) >= 2:
            current_time = self.get_clock().now()
            time_since_last_lap = (current_time - self.last_lap_time).nanoseconds / 1e9

            if time_since_last_lap > self.lap_cooldown_seconds:
                self.lap_count += 1
                self.last_lap_time = current_time
                self.get_logger().info(f"START/FINISH LINE CROSSED. Lap {self.lap_count}/{self.target_laps} started.")

                if self.lap_count >= self.target_laps:
                    self.get_logger().info("Target laps completed. Engaging failsafe: stopping the car.")
                    self.mission_finished = True
    def sendToControl(self) -> None:
        """Calculates the path locally and publishes it."""
        # Calculate path locking the car strictly to the local origin
        self.updateLapCount()
        if self.mission_finished:
            empty_path_msg = Path()
            empty_path_msg.header.stamp = self.get_clock().now().to_msg()
            empty_path_msg.header.frame_id = self.frameId
            self.publisher.publish(empty_path_msg)
            return
        
        self.path = self.pathPlanner.calculatePathInGlobalFrame(
            vehiclePosition=self.carPosition, 
            vehicleDirection=self.carDirection, 
            cones=self.cones
        )
        
        if self.path is not None and len(self.path) > 0:
            
            # 1. Strict Loop Filter: Remove any points that cause the path to bend backward (>90 degrees)
            # This guarantees the controller never gets confused by loops or zig-zags in sparse corners.
            if len(self.path) > 2:
                filtered_path = [self.path[0], self.path[1]]
                for j in range(2, len(self.path)):
                    v1 = filtered_path[-1] - filtered_path[-2]
                    v2 = self.path[j] - filtered_path[-1]
                    # If dot product is >= 0, angle is <= 90 deg (forward progress)
                    if np.dot(v1, v2) >= -0.01: # slight tolerance
                        filtered_path.append(self.path[j])
                self.path = np.array(filtered_path)

            # 2. Smooth the path if we have at least 3 points
            if len(self.path) >= 3:
                try:
                    # Simple Moving Average filter (window=3) to smooth angular corners
                    # without any risk of overshoots/loops that splines can cause.
                    window_size = min(3, len(self.path))
                    padded_path = np.pad(self.path, ((window_size//2, window_size//2), (0, 0)), mode='edge')
                    smoothed_path = np.zeros_like(self.path)
                    for i in range(len(self.path)):
                        smoothed_path[i] = np.mean(padded_path[i:i+window_size], axis=0)
                    self.path = smoothed_path
                except Exception as e:
                    self.get_logger().warning(f"Path smoothing failed: {e}. Using raw path.")

            # Publish path
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = self.frameId

            for i, dataPoint in enumerate(self.path):
                pose = Pose()
                pose.position.x = float(dataPoint[0])
                pose.position.y = float(dataPoint[1])
                pose.position.z = 0.0
                
                # Calculate yaw
                if i < len(self.path) - 1:
                    dx = float(self.path[i+1][0] - dataPoint[0])
                    dy = float(self.path[i+1][1] - dataPoint[1])
                elif len(self.path) > 1:
                    dx = float(dataPoint[0] - self.path[i-1][0])
                    dy = float(dataPoint[1] - self.path[i-1][1])
                else:
                    dx = 1.0
                    dy = 0.0
                
                yaw = math.atan2(dy, dx)
                pose.orientation.x = 0.0
                pose.orientation.y = 0.0
                pose.orientation.z = math.sin(yaw / 2.0)
                pose.orientation.w = math.cos(yaw / 2.0)

                #poseStamped = PoseStamped()
                #poseStamped.pose = pose
                #poseStamped.header.stamp = timestamp
                #poseStamped.header.frame_id = self.frameId
                #path_msg.poses.append(poseStamped)
                
                poseStamped = PoseStamped()
                poseStamped.pose = pose
                poseStamped.header.stamp = timestamp
                poseStamped.header.frame_id = self.frameId
                path_msg.poses.append(poseStamped)

            # Publish path in local frame (Fr1A) directly.
            # The simple pure pursuit controller expects a local frame path.
            self.publisher.publish(path_msg)

            self.visualize()

    def visualize(self) -> None:
        """Plots local cones and local path."""
        self.ax.clear()
        self.ax.set_title("Local Path Planning Visualization")
        self.ax.set_xlabel("X (m) [Forward]")
        self.ax.set_ylabel("Y (m) [Left]")
        self.ax.grid(True)

        # Plot Cones
        blue_cones = self.cones[ConeTypes.BLUE]
        yellow_cones = self.cones[ConeTypes.YELLOW]
        if blue_cones.shape[0] > 0:
            self.ax.plot(blue_cones[:, 0], blue_cones[:, 1], 'bo', label='Blue Cones', markersize=3)
        if yellow_cones.shape[0] > 0:
            self.ax.plot(yellow_cones[:, 0], yellow_cones[:, 1], 'yo', label='Yellow Cones', markersize=3)

        # Plot Path
        if self.path is not None and self.path.shape[0] > 0:
            self.ax.plot(self.path[:, 0], self.path[:, 1], 'r-', label='Local Path')

        # Plot Car
        self.ax.plot(self.carPosition[0], self.carPosition[1], 'ko', label='Car Origin')

        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

        

def main() -> None:
    rclpy.init()
    node = LocalPlanningNode()
  
   
    rate = node.create_rate(100)
    while rclpy.ok():
        #rclpy.spin_once(node)
        rclpy.spin(node)
        rate.sleep()
        
    node.get_logger().info("Shutting down Local Planning Node...")

if __name__ == "__main__":
    main()
