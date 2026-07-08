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
from ament_index_python.packages import get_package_share_directory
from .model import Seq2Seq
from planning_deep_learning import model
from tf_helper.StatusPublisher import StatusPublisher


class GlobalPlanningDlNode(Node):

    def __init__(self, modelPath: str):
        super().__init__("global_planning_dl")

        self.status = StatusPublisher("/status/planning_node", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()  

        # --- CAR STATE ---
        self.car_x = 0.0
        self.car_y = 0.0
        self.car_yaw = 0.0

        # Odom subscription
        self.odom_sub = self.create_subscription(
            Odometry,
            "/zed/zed_node/odom",
            self.odom_callback,
            10
        )

        self.get_logger().info("--- Initializing Tracking Mode ---")    
        self.get_logger().info(f" global_node")    
        try:
            self.model = model.createModel(modelPath)
            self.is_colorless = "colorless" in modelPath.lower()
            self.get_logger().info(f"Successfully loaded model from: {modelPath} (Colorless: {self.is_colorless})")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {str(e)}")

        self.path = None
        self.conesList = None

        # Setup Visualization
        # self.fig, self.ax = plt.subplots()
        # plt.show(block=False)
        
        self.subscriber1 = self.create_subscription(
            MarkerArray, "map/global_cones_markers", self.receiveFromPerception, 10)
        self.publisher = self.create_publisher(
            Path, "/path", 10)

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
        if self.path is None:
            self.path = []

        visible_cones = []

        cos_yaw = math.cos(self.car_yaw)
        sin_yaw = math.sin(self.car_yaw)

        for marker in msg.markers:
            # Cones in GLOBAL map frame
            xc = marker.pose.position.x
            yc = marker.pose.position.y

            # Translate to car origin
            dx = xc - self.car_x
            dy = yc - self.car_y

            # Rotate to local ROS frame (Fr1A: X is Forward, Y is Left)
            x_local = dx * cos_yaw + dy * sin_yaw
            y_local = -dx * sin_yaw + dy * cos_yaw

            # The Model expects: X is Right (Lateral), Y is Forward (Longitudinal).
            x_model = -y_local
            y_model = x_local

            # Calculate distance from the car (which is at 0,0 in this local frame)
            dist = math.hypot(x_model, y_model)

            # ==========================================================
            # OLD BOX FOV (Commented out as requested)
            # y_model is forward distance, x_model is lateral distance
            if y_model < 0.0 or y_model > 15.0 or x_model < - 4.0 or x_model > 4.0:
                continue
            # ==========================================================

            # # Filter 1: 15-meter radius
            # if dist > 15.0 or dist < 0.0:
            #     continue

            # # Filter 2: 60-degree forward semicircle (-60 to +60 degrees from forward axis)
            # # angle 0 is straight ahead (Y_model axis).
            # angle = math.atan2(x_model, y_model)
            # if abs(angle) > (math.pi / 3):
            #     continue

            r, g, b = marker.color.r, marker.color.g, marker.color.b

            # Classify cones from marker RGB (no namespace dependency).
            is_white = r > 0.95 and g > 0.95 and b > 0.95
            is_blue = b > 0.80 and g < 0.45 and r < 0.45
            is_yellow = r > 0.70 and g > 0.70 and b < 0.45

            if is_white:
                continue

            if self.is_colorless:
                if is_blue or is_yellow:
                    visible_cones.append((dist, [x_model, y_model]))
            else:
                if is_blue:
                    visible_cones.append((dist, [x_model, y_model, 1.0, 0.0]))
                elif is_yellow:
                    visible_cones.append((dist, [x_model, y_model, 0.0, 1.0]))

        # Sort all visible cones by distance to the car (this matches the notebook!)
        visible_cones.sort(key=lambda item: item[0])

        # Take the nearest 10 cones
        MAX_CONES = 10
        nearest_cones = visible_cones[:MAX_CONES]
        cones_features = [item[1] for item in nearest_cones]

        # --- TRACKING: PRINT CONE LIST ---
        if len(cones_features) > 0:
            # self.get_logger().info(f"--- FRAME START: {raw_count} Markers Received ---")
            # self.get_logger().info(f"Filtered Cones Entering Model ({len(cones_features)}):")
            for i, c in enumerate(cones_features):
                if self.is_colorless:
                    # self.get_logger().info(f"  [{i}] COLORLESS -> X: {c[0]:.3f}, Y: {c[1]:.3f}")
                    pass
                else:
                    color_label = "BLUE" if c[2] == 1.0 else "YELLOW"
                    # self.get_logger().info(f"  [{i}] {color_label} -> X: {c[0]:.3f}, Y: {c[1]:.3f}")
        else:
            self.get_logger().warn("No cones passed the ROI/Color filter.")
            return

        cones_array = np.array(cones_features, dtype=np.float32)
        
        feature_dim = 2 if self.is_colorless else 4
        # Pad if fewer than MAX_CONES (zeros at end)
        if len(cones_array) < MAX_CONES:
            pad = np.zeros((MAX_CONES - len(cones_array), feature_dim), dtype=np.float32)
            cones_array = np.concatenate([cones_array, pad], axis=0)

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.conesList = torch.tensor(cones_array, dtype=torch.float32).to(device)
        # self.conesList = torch.tensor(cones_array)
        
        self.send_to_control()

    def send_to_control(self):
        # 1. Run Prediction and detach immediately to avoid UserWarnings
        raw_prediction = self.model.predict(self.conesList)[0]
        self.path = raw_prediction.detach().cpu().numpy() # Convert to clean numpy array
        
        if self.path is not None:
            # --- TRACKING: PRINT PREDICTION DATA ---
            self.get_logger().info(f"Model Prediction (Path Points: {len(self.path)}):")
            self.get_logger().info(f"  First Point: X: {self.path[0][0]:.3f}, Y: {self.path[0][1]:.3f}")
            # self.get_logger().info(f"  Middle Pt:   X: {self.path[7][0]:.3f}, Y: {self.path[7][1]:.3f}")
            self.get_logger().info(f"  Last Point:  X: {self.path[-1][0]:.3f}, Y: {self.path[-1][1]:.3f}")
            
            timestamp = self.get_clock().now().to_msg()
            path_msg = Path()
            path_msg.header.stamp = timestamp
            path_msg.header.frame_id = "map" # Changed to map frame for global coordinates
            
            cos_yaw = math.cos(self.car_yaw)
            sin_yaw = math.sin(self.car_yaw)
            
            for dataPoint in self.path:
                pose = Pose()
                # Local ROS coordinates (Fr1A: X forward, Y left)
                x_local = float(dataPoint[1])
                y_local = -float(dataPoint[0])

                # Transform to Global Map coordinates
                x_global = self.car_x + (x_local * cos_yaw - y_local * sin_yaw)
                y_global = self.car_y + (x_local * sin_yaw + y_local * cos_yaw)
                
                pose.position.x = x_global
                pose.position.y = y_global

                pose_stamped = PoseStamped()
                pose_stamped.pose = pose
                pose_stamped.header.frame_id = "map"
                path_msg.poses.append(pose_stamped)

            self.publisher.publish(path_msg)
            self.get_logger().info("--- FRAME END: Path Published ---\n")
            
            # self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("Path Planning Live Tracking")
        self.ax.set_xlabel("X (Local)")
        self.ax.set_ylabel("Y (Forward)")
        self.ax.grid(True)

        # Re-extract coordinates for plotting from the tensor
        if self.is_colorless:
            cones = self.conesList.numpy()
            if len(cones) > 0:
                self.ax.plot(cones[:, 0], cones[:, 1], 'ko', markersize=6, label='Cones')
        else:
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
    model_file = os.path.join(get_package_share_directory('planning_deep_learning'), 'Completed_Models', 'best_model.pt')        
    node = GlobalPlanningDlNode(model_file)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()



