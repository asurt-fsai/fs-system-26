"""
this module is the controller node for the kinematic bicycle model.
The controller node subscribes to the state and path topics
The controller node publishes the steering angle and throttle to the respective topics.
It uses the adaptive pure pursuit algorithm to calculate the steering angle and throttle.
It also uses a PID controller to calculate the throttle based on the steering angle.

The controller node is implemented as a class with the following methods:

- initPubAndSub: Initializes the publishers and subscribers for the controller node.

- stateCallback: Callback function for the state subscriber.

- pathCallback: Callback function for the path subscriber.

- publishDrive: Publishes the drive message to the drive topic.

- main: Main function to initialize the controller node.

"""

import math
from typing import List
import rclpy
import time
from rclpy.node import Node
import rclpy.publisher
import matplotlib.pyplot as plt
from nav_msgs.msg import Odometry, Path
from tf_transformations import euler_from_quaternion
from ackermann_msgs.msg import AckermannDriveStamped
from .adaptive_purepursuit import AdaptivePurePursuit
from tf_helper.StatusPublisher import StatusPublisher
from std_msgs.msg import Float64


class Controller(Node):  # type: ignore[misc]
    """
    Controller class for the kinematic bicycle model.

    args:
        Node: rclpy node object

    functions:
        __init__: Initializes the controller node.

        declareTopics: Declares the topics for the controller node
        as parameters in the parameter server.

        initPubAndSub: Initializes the publishers and subscribers for the controller node.

        stateCallback: Callback function for the state subscriber.

        pathCallback: Callback function for the path subscriber.

        publishDrive: Publishes the drive message to the drive topic.

        main: Main function to initialize the controller node.

    """
    

    '''def plot_velocity_error(self) -> None:
        """
        Plots and saves a graph of the target vs actual speed over time.
        """
        import matplotlib.pyplot as plt

        if not self.time_log:
            self.get_logger().warn("No velocity data to plot.")
            return

        plt.figure()
        plt.plot(self.time_log, self.target_speed_log, label="Target Speed")
        plt.plot(self.time_log, self.actual_speed_log, label="Actual Speed")
        plt.xlabel("Time (s)")
        plt.ylabel("Speed (m/s)")
        plt.title("Velocity Tracking - Adaptive Pure Pursuit")
        plt.legend()
        plt.grid(True)

        self.get_logger().info("Saving velocity plot to file...")  # Added log message
        plt.savefig("/home/velocityError--Adaptive/velocity_tracking_plot.png")
        plt.close()'''
    

    def plot_velocity_error(self) -> None:
        if not self.time_log:
            self.get_logger().warn("No velocity data to plot.")
            return

        plt.figure()
        plt.plot(self.time_log, self.target_speed_log, label="Target Speed")
        plt.plot(self.time_log, self.actual_speed_log, label="Actual Speed")
        plt.xlabel("Time (s)")
        plt.ylabel("Speed (m/s)")
        plt.title("Velocity Tracking - Adaptive Pure Pursuit")
        plt.legend()
        plt.grid(True)

        # Create a filename based on current simulation time
        current_time = self.get_clock().now().nanoseconds / 1e9 - self.start_time
        filename = f"/home/fsai/velocityError--Adaptive/velocity_tracking_plot_{int(current_time)}s.png"

        self.get_logger().info(f"Saving velocity plot to {filename}")
        plt.savefig(filename)
        plt.close()


    def __init__(self) -> None:
        """
        Initializes the controller node with the name "controller" using the super() function.
        """
        super().__init__("Controller")
        self.purepursuit = AdaptivePurePursuit(self)
        self.declareTopics()
        self.initPubAndSub()
        self.drivePub: rclpy.publisher.Publisher
        self.time_log = [] #stores timestamps in sec relative to the start of the simulation.
        self.target_speed_log = [] #stores the target speeds from the controller
        self.actual_speed_log = [] # stores the actual speed of the vehicle from odometry data
        self.start_time = self.get_clock().now().nanoseconds / 1e9 #records the start time of the simulation
        self.latest_path_stamp = None


        self.status = StatusPublisher("/status/adaptive_pure_pursuit", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()


    def declareTopics(self) -> None:
        """
        Declare the topics for the controller node as parameters in the parameter server.

        topics:
            drive: Topic to publish the drive message
            state: Topic to subscribe to the state message
            path: Topic to subscribe to the path message
        """
        self.declare_parameter("drive", rclpy.Parameter.Type.STRING)
        self.declare_parameter("state", rclpy.Parameter.Type.STRING)
        self.declare_parameter("path", rclpy.Parameter.Type.STRING)
        self.get_logger().info("parameters declared")

    def initPubAndSub(self) -> None:
        """
        Initializes the publishers and subscribers for the controller node.

        topics:
            drive_topic: Topic to publish the drive message
            state_topic: Topic to subscribe to the state message
            path_topic: Topic to subscribe to the path message

        publishers:
            drivePub: Publisher for the drive message

        subscribers:
            stateSub: Subscriber for the state message
            pathSub: Subscriber for the path message

        timer:
            timer: Timer to publish the drive message
        """
        driveTopic = self.get_parameter("drive").get_parameter_value().string_value
        log = "drive topic : " + str(driveTopic)
        stateTopic = self.get_parameter("state").get_parameter_value().string_value
        log = log + "state topic : " + str(stateTopic)
        pathTopic = self.get_parameter("path").get_parameter_value().string_value
        log = log + "path topic : " + str(pathTopic)
        self.get_logger().info(log)

        self.drivePub = self.create_publisher(AckermannDriveStamped, driveTopic, 10)
        self.stateSub = self.create_subscription(Odometry, stateTopic, self.stateCallback, 10)
        self.pathSub = self.create_subscription(Path, pathTopic, self.pathCallback, 10)
        self.timer = self.create_timer(0.1, self.publishDrive)
        self.time_duration = self.create_publisher(Float64, '/diagnostics/comp_time/control', 10)

    def stateCallback(self, state: Odometry) -> None:
        """
        Callback function for the state subscriber.

        Args:
            state: Odometry message

        state:
            x: x position of the vehicle from the odometry message
            y: y position of the vehicle from the odometry message
            yaw: yaw angle of the vehicle from the odometry message
            velocity: velocity of the vehicle from the odometry message
        """
        velocityX: float = state.twist.twist.linear.x
        velocityY: float = state.twist.twist.linear.y
        orientationList: List[float] = [
            state.pose.pose.orientation.x,
            state.pose.pose.orientation.y,
            state.pose.pose.orientation.z,
            state.pose.pose.orientation.w,
        ]
        self.purepursuit.state = [
            #remove the comment when integrating with deep learining as they work with a diffrent frame
            0.0,
            0.0,
            0.0,
            
            #use this when using path csv
            # state.pose.pose.position.x,
            # state.pose.pose.position.y,
            # euler_from_quaternion(orientationList)[2],
    
            math.sqrt(velocityX**2 + velocityY**2),
        ]

    def pathCallback(self, path: Path) -> None:
        """
        Callback function for the path subscriber.pose

        Args:

            path: Path message

        path:
            waypoints: List of waypoints from the path message
        """
        self.latest_path_stamp = path.header.stamp

        self.purepursuit.waypoints = [
            (pose.pose.position.x, pose.pose.position.y) for pose in path.poses
        ]
        self.purepursuit.firstFlag = True

    def publishDrive(self) -> None:
        start_time = time.perf_counter()
        try:
                
            """
            Publishes the drive message to the drinodeve topic.

            driveMsg:
                AckermannDriveStamped message
                drive.steering_angle: steering angle calculated by the adaptive pure pursuit algorithm
                drive.speed: current vehicle's velocity plus throttle calculated by the PID controller

            steeringAngle:
                steering angle calculated by the adaptive pure pursuit algorithm

            throttle:
                throttle calculated by the PID controller
            """
            driveMsg = AckermannDriveStamped()
            if self.latest_path_stamp is not None:
                driveMsg.header.stamp = self.latest_path_stamp
            else:
                driveMsg.header.stamp = self.get_clock().now().to_msg()
            if len(self.purepursuit.waypoints) > 0:
                steeringAngle = self.purepursuit.angleCalc()
                driveMsg.drive.steering_angle = steeringAngle
                # Always compute throttle — don't stop at end of short local paths
                throttle = self.purepursuit.pidController(steeringAngle)
                driveMsg.drive.speed = self.purepursuit.state[3] + throttle
                current_time = self.get_clock().now().nanoseconds / 1e9 - self.start_time
                #record the following at every time step
                self.time_log.append(current_time)
                self.target_speed_log.append(self.purepursuit.targetSpeed)
                self.actual_speed_log.append(self.purepursuit.state[3])

            else:
                driveMsg.drive.steering_angle = self.purepursuit.steeringAngle
                driveMsg.drive.speed = self.purepursuit.state[3]
            log3 = str(abs(driveMsg.drive.speed))
            self.get_logger().info("current speed : " + log3)
            self.drivePub.publish(driveMsg)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000.0
            self.time_duration.publish(Float64(data=duration_ms))
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000.0
            self.time_duration.publish(Float64(data=duration_ms))


"""def main() -> None:
    #main function to initialize the controller node
    rclpy.init()
    controller = Controller()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown() """


def main() -> None:
    rclpy.init()
    controller = Controller()
    try:
        rclpy.spin(controller) #Reacting to stopping the node
    except KeyboardInterrupt:
        pass
    finally:
        # controller.plot_velocity_error()
        controller.destroy_node()
        rclpy.shutdown()

