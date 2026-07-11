


"""Module providing a function printing python version."""
# import time
import rclpy
from rclpy.node import Node
from planning_skidpad.SkidPadPathPlanningClass import SendPath
import numpy as np
import matplotlib.pyplot as plt
import math
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
# from asurt_msgs.msg import LandmarkArray
from cone_mapping.msg import LandmarkArray
from tf_helper.StatusPublisher import StatusPublisher

# import threading

# Cone type codes used throughout this node and by SendPath.getPath().
# NOTE: replace with a shared ConeTypes enum if one already exists in your
# codebase (e.g. from asurt_msgs / a common types module) - kept as plain
# ints here to avoid introducing an import that may not exist yet.
BLUE = 0
YELLOW = 1
ORANGE_SMALL = 2
ORANGE_BIG = 3
UNKNOWN = 4

# Marker.scale.z (height) threshold separating large orange cones (~0.505 m)
# from small orange / yellow / blue cones (~0.325 m). Determined empirically
# from recorded perception data.
LARGE_CONE_HEIGHT_THRESHOLD = 0.4


class SkidPadPathPlannerNode(Node):  # type: ignore[misc]
    """
    Class for generating a path for the skidpad.

    Attributes:
        pathGen (SendPath): The path generation object.
        finalPath (Path): The final path to be published.
        state (Odometry): The current state of the vehicle.
        conePositions (np.array): The positions of the cones.
    """

    def __init__(self) -> None:
        """
        Constructor for the SkidPadPathPlannerNode class.

        Args:
            None

        Returns:
            None
        """
        super().__init__("skidPadPathPlannerNode")

        self.status = StatusPublisher("/status/planning_skidpad", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()
        # Get parameters
        self.declare_parameters(
            namespace="",
            parameters=[
                ("pathTopic", rclpy.Parameter.Type.STRING),
                ("conesTopic", rclpy.Parameter.Type.STRING),
                ("stateTopic", rclpy.Parameter.Type.STRING),
            ],
        )
        pathTopic = self.get_parameter("pathTopic").get_parameter_value().string_value
        conesTopic = self.get_parameter("conesTopic").get_parameter_value().string_value
        stateTopic = self.get_parameter("stateTopic").get_parameter_value().string_value

        # Publishers
        self.pathPub = self.create_publisher(Path, pathTopic, 10)

        # Subscriptions
        self.create_subscription(LandmarkArray, conesTopic, self.listenerCallback, 10)
        self.create_subscription(Odometry, stateTopic, self.stateCallback, 10)

        # Initialize variables
        self.pathGen = SendPath()
        self.finalPath = Path()
        self.state = Odometry()
        self.conePositions = np.empty((0, 3))
        self.current_path_array = np.empty((0, 2))
        # self.timeStart = 0.0
        # self.timeStep = 0.0

        # Initialize matplotlib for real-time debugging
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.fig.canvas.manager.set_window_title("Skidpad Path Planner Debug")
        plt.show(block=False)

    def stateCallback(self, state: Odometry) -> None:
        """
        Callback function for handling state updates.

        Args:
            state (Odometry): The new state information.

        Returns:
            None
        """
        # Update the current state
        self.state = state
        if hasattr(self, 'current_path_array'):
            self.update_plot(self.current_path_array)

    

    def update_plot(self, path: np.ndarray) -> None:
        """
        Updates the real-time matplotlib visualization.
        """
        self.ax.clear()
        
        
        # Plot cones
        if self.conePositions.size > 0:
            blues = self.conePositions[self.conePositions[:, 2] == BLUE]
            yellows = self.conePositions[self.conePositions[:, 2] == YELLOW]
            small_oranges = self.conePositions[self.conePositions[:, 2] == ORANGE_SMALL]
            big_oranges = self.conePositions[self.conePositions[:, 2] == ORANGE_BIG]
            
            if blues.size > 0:
                self.ax.scatter(blues[:, 0], blues[:, 1], c='blue', marker='^', label='Blue')
            if yellows.size > 0:
                self.ax.scatter(yellows[:, 0], yellows[:, 1], c='y', marker='^', label='Yellow')
            if small_oranges.size > 0:
                self.ax.scatter(small_oranges[:, 0], small_oranges[:, 1], c='orange', marker='^', label='Small Orange')
            if big_oranges.size > 0:
                self.ax.scatter(big_oranges[:, 0], big_oranges[:, 1], c='darkorange', marker='s', s=100, label='Big Orange')

        # Plot origin and centers
        origin = self.pathGen.origin
        left_center = self.pathGen.leftCenter
        right_center = self.pathGen.rightCenter
        
        if origin is not None and not np.array_equal(origin, [0, 0]):
            self.ax.scatter(origin[0], origin[1], c='red', marker='x', s=100, label='Origin')
        if left_center is not None:
            self.ax.scatter(left_center[0], left_center[1], c='magenta', marker='x', s=100, label='Left Center')
        if right_center is not None:
            self.ax.scatter(right_center[0], right_center[1], c='cyan', marker='x', s=100, label='Right Center')

        # Plot car position
        car_x = self.state.pose.pose.position.x
        car_y = self.state.pose.pose.position.y
        self.ax.scatter(car_x, car_y, c='black', marker='o', s=100, label='Car')
        
        # Plot generated path
        if path is not None and len(path) > 0:
            self.ax.plot(path[:, 0], path[:, 1], 'g-', linewidth=2, label='Path')

        self.ax.set_title(f"Skidpad Planner - Phase Count: {self.pathGen.count}")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.axis('equal')
        self.ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.pause(0.001)

    def listenerCallback(self, landmarkMsg: LandmarkArray) -> None:
        """
        Callback function for handling MarkerArray messages.

        Args:
            poseArrayMsg (MarkerArray): The incoming MarkerArray message.

        Returns:
            None
        """
        # Extract cone positions, classifying each cone by color/size
        # instead of using the raw (unreliable) marker.type field.
        new_cone_positions_list = []

        for landmark in landmarkMsg.landmarks:
            new_cone_positions_list.append([
                landmark.position.x,
                landmark.position.y,
                landmark.type
            ])

        new_cone_positions = np.array(new_cone_positions_list)

        if new_cone_positions.size == 0:
            return

        # self.conePositions = np.append(
        #     self.conePositions,
        #     new_cone_positions,
        #     axis=0,
        # )
        self.conePositions = new_cone_positions

        # Generate the path
        self.finalPath.poses = []
        # self.timeStart = time.time()
        path = self.pathGen.getPath(self.state, self.conePositions)
        # self.timeStep = time.time() - self.timeStart
        # self.get_logger().info(f"path is {path} ")
        # self.get_logger().info(f"time_step is {self.timeStep} ")

        if path is None:
            return

        self.current_path_array = path

        # Convert the path to PoseStamped messages and publish it
        for i in path:
            pose = PoseStamped()
            pose.pose.position.x = float(i[0])
            pose.pose.position.y = float(i[1])
            self.finalPath.poses.append(pose)
        self.finalPath.header.frame_id = "map"
        self.pathPub.publish(self.finalPath)


def main() -> None:
    """
    Main function that initializes the program and executes the path generation.

    Args:
        args: Command-line arguments.

    Returns:
        None
    """
    # Initialize the ROS2 node
    rclpy.init()
    # Create the path generation node
    skidPad = SkidPadPathPlannerNode()
    # Spin in a separate thread
    # thread = threading.Thread(target=rclpy.spin, args=(SkidPad, ), daemon=True)
    # thread.start()
    # Spin the node
    rclpy.spin(skidPad)
    # Destroy the node
    skidPad.destroy_node()
    # Shutdown the ROS2 client library
    rclpy.shutdown()


if __name__ == "__main__":
    main()