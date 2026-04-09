#!/usr/bin/env python3

import os
import sys
import numpy as np
import torch
import matplotlib.pyplot as plt
from rclpy.node import Node
import rclpy
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Path
from geometry_msgs.msg import Pose, PoseStamped
from nav_msgs.msg import Odometry
import math
from .model import Seq2Seq
from planning_deep_learning import model

class PlanningDlNode(Node):

    def __init__(self, modelPath: str):
        super().__init__("planning_dl")  

        # --- CAR STATE ---
        self.car_x = 0.0
        self.car_y = 0.0
        self.car_yaw = 0.0

        # Odom subscription - Updated to the correct ZED odom topic
        self.odom_sub = self.create_subscription(
            Odometry,
            "/zed/zed_node/odom",
            self.odom_callback,
            10
        )

        self.get_logger().info("--- Initializing Tracking Mode ---")        
        model_file = "/home/eyad/Desktop/Testing_SLAM/src/SLAM_Camera/src/deep learning/planning_deep_learning/planning_deep_learning/best_HybridgedanconeshiftingRFIX2.pth"
        
        try:
            self.model = model.createModel(model_file)
            self.get_logger().info(f"Successfully loaded model from: {model_file}")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {str(e)}")

        self.path = None
        self.conesList = None

        # Setup Visualization
        self.fig, self.ax = plt.subplots()
        plt.show(block=False)
        
        self.subscriber1 = self.create_subscription(
            MarkerArray, "/map/global_cones_markers", self.receiveFromPerception, 1)
        self.publisher = self.create_publisher(
            Path, "/topic2", 10)

    def odom_callback(self, msg: Odometry):
        self.car_x = msg.pose.pose.position.x
        self.car_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.car_yaw = math.atan2(siny_cosp, cosy_cosp)

        self.get_logger().info(f"Car yaw: {math.degrees(self.car_yaw):.2f} deg")


    def receiveFromPerception(self, msg: MarkerArray) -> None:
        raw_count = len(msg.markers)
        
        cones = []
        for marker in msg.markers:

            # Cones in MAP frame
            xc = marker.pose.position.x
            yc = marker.pose.position.y

            # Translate to car origin
            dx = xc - self.car_x
            dy = yc - self.car_y

            # Rotate to car frame
            x_rel =  math.cos(self.car_yaw)*dx + math.sin(self.car_yaw)*dy
            y_rel = -math.sin(self.car_yaw)*dx + math.cos(self.car_yaw)*dy

            # Swap to match your old model format
            y, x = x_rel, -y_rel
                        # ROI Filtering 
            if x > 4 or y > 20 or x < -4 or y < 0: 
                continue

    # # --- PIZZA SLICE ROI FILTERING ---
    #         max_radius = 10.0
    #         center_angle = 90.0  # Pointing straight ahead on the Y-axis
    #         angle_width = 90.0   # Total FOV width
            
    #         distance = math.sqrt(x**2 + y**2)
    #         point_angle = math.degrees(math.atan2(y, x))
            
    #         is_in_radius = distance <= max_radius
    #         is_in_angle = abs(point_angle - center_angle) <= (angle_width / 2)

    #         if not (is_in_radius and is_in_angle):
    #             continue

            ns_lower = marker.ns.lower()
            # Color Identification & One-Hot Encoding
            r, g, b = marker.color.r, marker.color.g, marker.color.b
            if r == 1.0 and g == 1.0 and b == 0.0:  # Yellow
                # One-hot: [x, y, 0, 1] for Yellow
                cones.append(np.array([x, y, 0, 1]))
            elif r == 0.0 and g == 0.0 and b == 1.0:  # Blue
                # One-hot: [x, y, 1, 0] for Blue
                cones.append(np.array([x, y, 1, 0])) 

        # --- TRACKING: PRINT CONE LIST ---
        if len(cones) > 0:
            self.get_logger().info(f"--- FRAME START: {raw_count} Markers Received ---")
            self.get_logger().info(f"Filtered Cones Entering Model ({len(cones)}):")
            for i, c in enumerate(cones):
                color_label = "BLUE" if c[2] == 1 else "YELLOW"
                self.get_logger().info(f"  [{i}] {color_label} -> X: {c[0]:.3f}, Y: {c[1]:.3f}")
        else:
            self.get_logger().warn("No cones passed the ROI/Color filter.")
            return

        cones_array = np.array(cones, dtype=np.float32)
        self.conesList = torch.tensor(cones_array)
        
        self.send_to_control()

    def send_to_control(self):
        # 1. Run Prediction and detach immediately to avoid UserWarnings
        raw_prediction = self.model.predict(self.conesList)[0]
        self.path = raw_prediction.detach().cpu().numpy() # Convert to clean numpy array
        
        if self.path is not None:
            # --- TRACKING: PRINT PREDICTION DATA ---
            self.get_logger().info(f"Model Prediction (Path Points: {len(self.path)}):")
            if len(self.path) > 0:
                self.get_logger().info(f"  First Point: X: {self.path[0][0]:.3f}, Y: {self.path[0][1]:.3f}")
                mid_idx = len(self.path) // 2
                self.get_logger().info(f"  Middle Pt:   X: {self.path[mid_idx][0]:.3f}, Y: {self.path[mid_idx][1]:.3f}")
                self.get_logger().info(f"  Last Point:  X: {self.path[-1][0]:.3f}, Y: {self.path[-1][1]:.3f}")
            
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = "base_link"  # Attach to the car's local frame
            
            for dataPoint in self.path:
                pose = Pose()
                
                # Model output to local ROS coordinates
                # Since the path is now attached to the car frame, we don't need to add the car's global position.
                pose.position.x = float(dataPoint[1])
                pose.position.y = -float(dataPoint[0])
                
                # Keep Z on the ground
                pose.position.z = 0.0

                pose_stamped = PoseStamped()
                pose_stamped.pose = pose
                pose_stamped.header.frame_id = "base_link"
                path_msg.poses.append(pose_stamped)

            self.publisher.publish(path_msg)
            self.get_logger().info("--- FRAME END: Path Published ---\n")
            
            self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("Path Planning Live Tracking")
        self.ax.set_xlabel("X (Local)")
        self.ax.set_ylabel("Y (Forward)")
        self.ax.grid(True)

        # Re-extract coordinates for plotting from the tensor
        blue_cones = self.conesList[self.conesList[:, 2] == 1][:, :2]
        yellow_cones = self.conesList[self.conesList[:, 3] == 1][:, :2]
        
        if len(blue_cones) > 0:
            self.ax.plot(blue_cones[:, 0], blue_cones[:, 1], 'bo', markersize=6, label='Blue Cones')
        if len(yellow_cones) > 0:
            self.ax.plot(yellow_cones[:, 0], yellow_cones[:, 1], 'yo', markersize=6, label='Yellow Cones')

        # Plot predicted trajectory
        self.ax.plot(self.path[:, 0], self.path[:, 1], 'r-', linewidth=2, label='Predicted Path')
        self.ax.scatter(self.path[:, 0], self.path[:, 1], c='red', s=10) # Individual points

        self.ax.legend(loc='upper right')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

def main(args=None):
    rclpy.init(args=args)
    model_file = "/home/eyad/Desktop/Testing_SLAM/src/SLAM_Camera/src/deep learning/planning_deep_learning/planning_deep_learning/best_HybridgedanconeshiftingRFIX2.pth"
    node = PlanningDlNode(model_file)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user.")
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()