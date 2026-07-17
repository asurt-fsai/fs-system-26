#!/usr/bin/env python3
"""
Skidpad Hardcoded Path Planner Node
===================================
Generates and publishes an exact, mathematically precise figure-of-eight
path based on the Formula Student rules:
1. Entry lane: starts 15m before start/finish (X: 0.0 to 15.0).
2. Right circle: radius 9.125m, center (15.0, -9.125). 2 clockwise laps.
3. Left circle: radius 9.125m, center (15.0, 9.125). 2 counter-clockwise laps.
4. Exit lane: X: 15.0 to 40.0. Full stop.

Features:
- Supports both PoseStamped and Odometry messages (highly adaptable for Isaac Sim, CarMaker, or real vehicle).
- Automatic Path Alignment: Rotates and translates the hardcoded path dynamically based on the vehicle's 
  spawn/staging position, making it fully plug-and-play anywhere in any simulator.
"""
import os
import math
import time
import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Pose, PoseStamped, PoseWithCovarianceStamped
from ackermann_msgs.msg import AckermannDriveStamped
from tf_helper.StatusPublisher import StatusPublisher
from std_msgs.msg import Float64


class SkidpadHardcodedPlanner(Node):
    def __init__(self):
        super().__init__("skidpad_hardcoded_planner")

        # --- Parameters ---
        self.declare_parameter("origin_x", 15.0)
        self.declare_parameter("origin_y", 0.0)
        self.declare_parameter("radius_mean", 9.125)
        self.declare_parameter("publish_rate", 20.0)  # 20 Hz
        self.declare_parameter("use_odom", False)  # Set to True to subscribe to Odometry instead of PoseStamped
        self.declare_parameter("pose_topic", "/zed/zed_node/pose")
        self.declare_parameter("odom_topic", "/zed/zed_node/odom")
        self.declare_parameter("align_to_initial_pose", True)  # Shift/rotate path to match car spawn pose
        self.declare_parameter("status_topic", "/status/planning_skidpad_hardcoded")

        self.origin_x = self.get_parameter("origin_x").value
        self.origin_y = self.get_parameter("origin_y").value
        self.radius_mean = self.get_parameter("radius_mean").value
        self.use_odom = self.get_parameter("use_odom").value
        self.pose_topic = self.get_parameter("pose_topic").value
        self.odom_topic = self.get_parameter("odom_topic").value
        self.align_to_initial_pose = self.get_parameter("align_to_initial_pose").value

        # --- Vehicle State ---
        self.car_x = 0.0
        self.car_y = 0.0
        self.car_yaw = 0.0

        # --- Path Initialization ---
        self.global_path = self.generate_skidpad_path()
        self.current_idx = 0
        self.finished = False

        # Transform tracking
        self.initial_pose_received = False
        self.initial_x = 0.0
        self.initial_y = 0.0
        self.initial_yaw = 0.0

        # --- Subscriptions & Publishers ---
        if self.use_odom:
            self.odom_sub = self.create_subscription(
                Odometry, self.odom_topic, self.odom_callback, 10
            )
            self.get_logger().info(f"Subscribed to Odometry on: {self.odom_topic}")
        else:
            self.pose_sub = self.create_subscription(
                PoseStamped, self.pose_topic, self.pose_callback, 10
            )
            self.get_logger().info(f"Subscribed to PoseStamped on: {self.pose_topic}")
        
        self.path_pub = self.create_publisher(Path, "/path", 10)
        
        # Stop command publishers
        self.cmd_pub = self.create_publisher(AckermannDriveStamped, "/cmd", 10)
        self.ackr_pub = self.create_publisher(AckermannDriveStamped, "/ackr", 10)

        # Time diagnostic publisher
        self.time_duration = self.create_publisher(Float64, "/diagnostics/comp_time/skidpad_hardcoded_planner", 10)

        # --- Heartbeat / Status Publisher ---
        status_topic_val = self.get_parameter("status_topic").value
        self.status = StatusPublisher(status_topic_val, self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.heartbeat_callback)
        self.status.ready()

        # --- Timer to update and publish the path ---
        dt = 1.0 / self.get_parameter("publish_rate").value
        self.timer = self.create_timer(dt, self.update_path)

        self.get_logger().info("--- Skidpad Hardcoded Planner Node Started ---")
        self.get_logger().info(f"Generated {len(self.global_path)} waypoints for complete figure-8 event.")
        if self.align_to_initial_pose:
            self.get_logger().info("Waiting for first pose/odom to dynamically align the path...")

    def pose_callback(self, msg: PoseStamped):
        self.car_x = msg.pose.position.x
        self.car_y = msg.pose.position.y
        
        q = msg.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.car_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.check_and_align_path()

    def odom_callback(self, msg: Odometry):
        self.car_x = msg.pose.pose.position.x
        self.car_y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.car_yaw = math.atan2(siny_cosp, cosy_cosp)

        self.check_and_align_path()

    def check_and_align_path(self):
        if self.align_to_initial_pose and not self.initial_pose_received:
            self.initial_x = self.car_x
            self.initial_y = self.car_y
            self.initial_yaw = self.car_yaw
            self.initial_pose_received = True

            # Transform the relative path by rotating and translating it
            cos_y = math.cos(self.initial_yaw)
            sin_y = math.sin(self.initial_yaw)

            transformed_pts = []
            for pt in self.global_path:
                x_rel, y_rel = pt[0], pt[1]
                x_new = self.initial_x + (x_rel * cos_y - y_rel * sin_y)
                y_new = self.initial_y + (x_rel * sin_y + y_rel * cos_y)
                transformed_pts.append([x_new, y_new])

            self.global_path = np.array(transformed_pts, dtype=np.float32)
            self.get_logger().info(
                f"Dynamically aligned hardcoded path to spawn/staging pose: "
                f"X={self.initial_x:.3f}, Y={self.initial_y:.3f}, Yaw={self.initial_yaw:.3f}"
            )

    def heartbeat_callback(self):
        if self.finished:
            self.status.ready()
        else:
            self.status.running()

    def generate_skidpad_path(self) -> np.ndarray:
        pts = []

        # 1. Entry Lane: X from 0.0 to origin_x (15.0), Y = 0.0
        # Spacing of 0.05 meters
        # Changed to 0.5 meters
        for x in np.arange(0.0, self.origin_x, 0.5):
            pts.append([x, self.origin_y])

        # 2. Right Circle (Clockwise, 2 Laps)
        # Center: (origin_x, origin_y - radius_mean)
        # Starts at angle = pi/2, goes to -3.5*pi (2 laps)
        right_cx = self.origin_x
        right_cy = self.origin_y - self.radius_mean
        t_right = np.arange(math.pi / 2.0, -3.5 * math.pi, -0.01)
        for t in t_right:
            x = right_cx + self.radius_mean * math.cos(t)
            y = right_cy + self.radius_mean * math.sin(t)
            pts.append([x, y])

        # 3. Left Circle (Counter-Clockwise, 2 Laps)
        # Center: (origin_x, origin_y + radius_mean)
        # Starts at angle = -pi/2, goes to 3.5*pi (2 laps)
        left_cx = self.origin_x
        left_cy = self.origin_y + self.radius_mean
        t_left = np.arange(-math.pi / 2.0, 3.5 * math.pi, 0.01)
        for t in t_left:
            x = left_cx + self.radius_mean * math.cos(t)
            y = left_cy + self.radius_mean * math.sin(t)
            pts.append([x, y])

        # 4. Exit Lane: X from origin_x (15.0) to 40.0, Y = 0.0
        for x in np.arange(self.origin_x, 40.0, 0.05):
            pts.append([x, self.origin_y])

        return np.array(pts, dtype=np.float32)

    def update_path(self):
        start_time = time.perf_counter()

        if self.finished:
            # Send stop command repeatedly to make sure vehicle remains stopped
            self.send_stop_command()
            return

        # If we require alignment but haven't received initial pose yet, don't publish the path
        if self.align_to_initial_pose and not self.initial_pose_received:
            return

        # 1. Update moving window index
        # Search a window of 80 points ahead of the current index
        search_window = self.global_path[self.current_idx : self.current_idx + 80]
        if len(search_window) > 0:
            dists = np.linalg.norm(search_window - np.array([self.car_x, self.car_y]), axis=1)
            min_local_idx = np.argmin(dists)
            # Advance index
            self.current_idx += min_local_idx

        # 2. Check if we reached the end of the exit lane
        # If we are within 40 points of the end (about 2 meters), trigger finished state
        if self.current_idx >= len(self.global_path) - 40:
            self.finished = True
            self.get_logger().info("--- EVENT COMPLETE: STOPPING VEHICLE ---")
            self.send_stop_command()
            return

        # 3. Extract and publish path slice starting from current index
        path_slice = self.global_path[self.current_idx : self.current_idx + 120]
        
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = "map"

        for pt in path_slice:
            pose_stamped = PoseStamped()
            pose_stamped.pose.position.x = float(pt[0])
            pose_stamped.pose.position.y = float(pt[1])
            pose_stamped.pose.position.z = 0.0
            pose_stamped.pose.orientation.w = 1.0
            pose_stamped.header.stamp = path_msg.header.stamp
            pose_stamped.header.frame_id = "map"
            path_msg.poses.append(pose_stamped)

        self.path_pub.publish(path_msg)

        # Publish execution duration
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self.time_duration.publish(Float64(data=duration_ms))

    def send_stop_command(self):
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.drive.speed = 0.0
        msg.drive.steering_angle = 0.0
        # self.cmd_pub.publish(msg)
        # self.ackr_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SkidpadHardcodedPlanner()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
