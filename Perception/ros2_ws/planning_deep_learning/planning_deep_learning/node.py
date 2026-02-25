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

# Paths updated to your workspace
#sys.path.append('/home/ayasx9/FSAI26/deep/FSAI_Workspace/src/planning_node/dependencies/tf_helper/')
from tf_helper import TFHelper
from .model import Seq2Seq
from planning_deep_learning import model

class PlanningDlNode(Node):

    def __init__(self, modelPath: str):
        super().__init__("planning_dl")
        
        self.get_logger().info("--- Initializing Tracking Mode ---")
        
        model_file = "/home/ayasx9/FSAI26/FSAI25_perception/fs-system-26/Perception/ros2_ws/planning_deep_learning/planning_deep_learning/best_HybridgedanconeshiftingRFIX.pth"
        
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

        self.tfhelper = TFHelper.TFHelper(self)
        
        self.subscriber1 = self.create_subscription(
            MarkerArray, "/perception_markers", self.receiveFromPerception, 1)
        self.publisher = self.create_publisher(
            Path, "/topic2", 10)

    def receiveFromPerception(self, msg: MarkerArray) -> None:
        raw_count = len(msg.markers)
        msg = self.tfhelper.transformMsg(msg, "zed_left_camera_frame")
        
        cones = []
        for marker in msg.markers:
            ns_lower = marker.ns.lower()
            # Coordinate mapping
            y, x = marker.pose.position.x, -marker.pose.position.y
            r, g, b = marker.color.r, marker.color.g, marker.color.b

            # ROI Filtering
            if x > 6 or y > 15 or x < -6 or y < 0:
                continue

            # Color Identification & One-Hot Encoding
            #if "yellow" in ns_lower:
                # One-hot: [x, y, 0, 1] for Yellow
            if r ==1 and g==1 and b ==0:
                cones.append(np.array([x, y, 0, 1]))
            #elif "blue" in ns_lower:
                # One-hot: [x, y, 1, 0] for Blue
            if r ==0 and g==0 and b ==1:
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
            self.get_logger().info(f"  First Point: X: {self.path[0][0]:.3f}, Y: {self.path[0][1]:.3f}")
            self.get_logger().info(f"  Middle Pt:   X: {self.path[7][0]:.3f}, Y: {self.path[7][1]:.3f}")
            self.get_logger().info(f"  Last Point:  X: {self.path[-1][0]:.3f}, Y: {self.path[-1][1]:.3f}")
            
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = "zed_left_camera_frame" # Frame corrected to prevent TF loop errors
            
            for dataPoint in self.path:
                pose = Pose()
                # Mapping model output to ROS coordinates
                pose.position.y = -float(dataPoint[0])
                pose.position.x = float(dataPoint[1])

                pose_stamped = PoseStamped()
                pose_stamped.pose = pose
                pose_stamped.header.frame_id = "zed_left_camera_frame"
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
    model_file = "/home/ayasx9/FSAI26/FSAI25_perception/fs-system-26/Perception/ros2_ws/planning_deep_learning/planning_deep_learning/best_HybridgedanconeshiftingRFIX.pth"
    node = PlanningDlNode(model_file)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user.")
    finally:
        rclpy.shutdown()
if __name__ == '__main__':
    main()