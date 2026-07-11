#!/usr/bin/env python3
"""
Acceleration path planning node
This node is responsible for starting the path planning module for the acceleration mission
"""

import matplotlib.pyplot as plt
from typing import Any, List
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import Pose, PoseStamped
import numpy as np
from numpy.typing import NDArray
from tf_transformations import euler_from_quaternion
from visualization_msgs.msg import MarkerArray, Marker

# Using the ROS 2 isolated package import
from planning_acceleration.calculate_path import CalculatePath, ConeTypes
from tf_helper.StatusPublisher import StatusPublisher

FloatArray = NDArray[np.float_]


class AccPlanningNode(Node):
    """
    A class representing a planning node.

    This node is responsible for receiving data from perception and localization,
    calculating a path based on the received data, and sending the path to control.
    """

    def __init__(self) -> None:
        super().__init__("acceleration_node")
        self.get_logger().info("Acceleration Planner instantiated...")
        self.status = StatusPublisher("/status/planning_acceleration", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()

        self.path: FloatArray = np.zeros((0, 2))
        self.cones: List[FloatArray] = [np.zeros((0, 2)) for _ in ConeTypes]
        self.carPosition = np.array([0.0, 0.0])
        self.carDirection = np.float_(0.0)

        # Matplotlib Visualization Setup
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Acceleration Path Planning Visualization")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.grid(True)
        plt.show(block=False)

        self.publisher: rclpy.publisher.Publisher

        self.declareParameters()
        self.setParameters()
        self.initPubAndSub()

        self.calculatePath = CalculatePath(self.carPosition, self.carDirection, self.cones)

    def declareParameters(self) -> None:
        """
        Declare the parameters for the planning node.
        """
        self.declare_parameter("acceleration.topics.frame_id", rclpy.Parameter.Type.STRING)
        self.declare_parameter("acceleration.topics.pathTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("acceleration.topics.odometryTopic", rclpy.Parameter.Type.STRING)
        self.declare_parameter("acceleration.topics.conesTopic", rclpy.Parameter.Type.STRING)

    def setParameters(self) -> None:
        """
        Get parameters from the parameter server and set them to their respective varibles
        """
        self.frameId = (
            self.get_parameter("acceleration.topics.frame_id").get_parameter_value().string_value
        )

    def initPubAndSub(self) -> None:
        """
        Initialize Publishers and subscribers for planning node
        """
        pathTopic = self.get_parameter("acceleration.topics.pathTopic").get_parameter_value().string_value
        odometryTopic = self.get_parameter("acceleration.topics.odometryTopic").get_parameter_value().string_value
        conesTopic = self.get_parameter("acceleration.topics.conesTopic").get_parameter_value().string_value
        
        self.publisher = self.create_publisher(Path, pathTopic, 10)
        self.subscriber1 = self.create_subscription(MarkerArray, conesTopic, self.receiveFromPerception, 10)
        self.subscriber2 = self.create_subscription(Odometry, odometryTopic, self.receiveFromLocalization, 10)
        

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        """
        Receives data from perception.
        """
        self.cones = [np.zeros((0, 2)) for _ in ConeTypes]
        
        cos_yaw = np.cos(self.carDirection)
        sin_yaw = np.sin(self.carDirection)
        
        for marker in msg.markers:
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            local_x, local_y = marker.pose.position.x, marker.pose.position.y
            
            #REVIEW ROTATION MATRIX, WHETHER IT IS CORRECT, WHY ASLN, REMOVE IN ISAACSIM?
            x = local_x * cos_yaw - local_y * sin_yaw + self.carPosition[0]
            y = local_x * sin_yaw + local_y * cos_yaw + self.carPosition[1]

            if r > 0.95 and g > 0.95 and b > 0.95:
                cone_type = ConeTypes.UNKNOWN
            
            # Catch the exact R=1.0, G=0.6, B=0.0 from CarMaker (Orange Cones)
            #CHECK AND TEST ON ISAAC - 
            elif r > 0.9 and g > 0.5 and b < 0.1:
                # cone_type = ConeTypes.ORANGE_BIG
                cone_type = ConeTypes.UNKNOWN
  
            elif g > 0.7:  # Yellow Cone
                cone_type = ConeTypes.YELLOW
                #cone_type = ConeTypes.UNKNOWN
                
            elif b > 0.7:  # Blue Cone
                cone_type = ConeTypes.BLUE
                #cone_type = ConeTypes.UNKNOWN
                
            else:
                cone_type = ConeTypes.UNKNOWN
                
            # Append position to the corresponding cone type
            self.cones[cone_type] = np.vstack((self.cones[cone_type], np.array([x, y])))

        self.classify_unknown_cones()
        self.sendToControl()

    def classify_unknown_cones(self) -> None:
        """
        Geometrically classify UNKNOWN cones as BLUE (left) or YELLOW (right)
        based on the car's current heading.
        """
        unknown_cones = self.cones[ConeTypes.UNKNOWN]
        if unknown_cones.shape[0] == 0:
            return
            
        car_dir_vec = np.array([np.cos(self.carDirection), np.sin(self.carDirection)])
        
        for cone in unknown_cones:
            car_to_cone = cone - self.carPosition
            cross_product = np.cross(car_dir_vec, car_to_cone)
            
            #REVIEW CROSS PRODUCT
            # If cross_product < 0, cone is on the right (YELLOW). Otherwise left (BLUE).
            if cross_product < 0:
                self.cones[ConeTypes.YELLOW] = np.vstack((self.cones[ConeTypes.YELLOW], cone))
            else:
                self.cones[ConeTypes.BLUE] = np.vstack((self.cones[ConeTypes.BLUE], cone))
                
        # Clear the UNKNOWN cones since they are now classified
        self.cones[ConeTypes.UNKNOWN] = np.zeros((0, 2))

    def receiveFromLocalization(self, msg: Odometry) -> None:
        """
        Receives data from localization.
        Updates the global position and heading (yaw) of the car.
        """
        pose = msg.pose.pose
        orientationQ = pose.orientation
        self.carPosition = np.array([pose.position.x, pose.position.y])

        orientationList = [orientationQ.x, orientationQ.y, orientationQ.z, orientationQ.w]
        (_, _, yaw) = euler_from_quaternion(orientationList)
        self.carDirection = yaw

    def sendToControl(self) -> None:
        """
        Sends the calculated path to control.
        """

            
        self.calculatePath.updateInput(self.carPosition, self.carDirection, self.cones)
        self.path = self.calculatePath.getPath()

        if self.path is not None:
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
            
        # Trigger the plot update
        self.visualize()

    def visualize(self) -> None:
        """Plots the local map state, cones, and path."""
        self.ax.clear()
        self.ax.set_title("Acceleration Path Planning")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.grid(True)

        # Plot Cones
        blue_cones = self.cones[ConeTypes.BLUE]
        yellow_cones = self.cones[ConeTypes.YELLOW]
        orange_cones = self.cones[ConeTypes.ORANGE_BIG]

        if blue_cones.shape[0] > 0:
            self.ax.plot(blue_cones[:, 0], blue_cones[:, 1], 'bo', label='Blue Cones', markersize=4)
        if yellow_cones.shape[0] > 0:
            self.ax.plot(yellow_cones[:, 0], yellow_cones[:, 1], 'yo', label='Yellow Cones', markersize=4)
        if orange_cones.shape[0] > 0:
            self.ax.plot(orange_cones[:, 0], orange_cones[:, 1], 'o', color='orange', label='Orange Cones', markersize=5)

        # Plot Calculated Path
        if self.path is not None and self.path.shape[0] > 0:
            self.ax.plot(self.path[:, 0], self.path[:, 1], 'r-', label='Centerline Path')

        # Plot Car Pose
        self.ax.plot(self.carPosition[0], self.carPosition[1], 'ko', label='Car Position')
        
        # Arrow for Car Heading
        dx = np.cos(self.carDirection) * 1.5
        dy = np.sin(self.carDirection) * 1.5
        self.ax.arrow(self.carPosition[0], self.carPosition[1], dx, dy, head_width=0.5, head_length=0.5, fc='k', ec='k')

        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)


def main(args: Any = None) -> None:
    """
    Initializes ROS, creates PlanningNode, spins, & shuts down.
    """
    rclpy.init(args=args)
    node = AccPlanningNode()

    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
