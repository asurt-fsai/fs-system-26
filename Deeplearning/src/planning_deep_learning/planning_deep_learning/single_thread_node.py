#!/usr/bin/env python3
"""
Planning Deep-Learning Node — Synchronous Architecture
======================================================
TensorRT inference runs directly within the ROS 2 node's main thread.
The perception callback processes the cones, runs the model, and
publishes the path sequentially.
"""

import os
import math
import numpy as np

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray
from nav_msgs.msg import Path
from geometry_msgs.msg import Pose, PoseStamped
from ament_index_python.packages import get_package_share_directory
from tf_helper.StatusPublisher import StatusPublisher
import time
from std_msgs.msg import Float64

# PyCUDA and TensorRT imports
import pycuda.driver as cuda
import tensorrt as trt
from planning_deep_learning.tensorrt_model import TensorRTModel


class PlanningDlNode(Node):

    def __init__(self, model_path: str):
        super().__init__("planning_dl")

        # --- Model metadata --------------------------------------------------
        self.is_colorless = "colorless" in model_path.lower()
        self.get_logger().info("--- Initializing TensorRT Planning Node (Synchronous) ---")
        self.get_logger().info(f"Engine : {model_path}")
        self.get_logger().info(f"Colorless: {self.is_colorless}")

        # --- Initialize PyCUDA and TensorRT ----------------------------------
        cuda.init()
        self.cuda_device = cuda.Device(0)
        self.cuda_context = self.cuda_device.make_context()
        np.bool = np.bool_  # numpy compat fix

        self.get_logger().info("Loading TensorRT engine...")
        self.model = TensorRTModel(model_path)
        self.get_logger().info("✅ TensorRT engine READY.")

        # --- Status / Heartbeat ----------------------------------------------
        self.status = StatusPublisher("/status/planning_node", self)
        self.status.starting()
        self.status_timer = self.create_timer(
            0.1,  # 10 Hz heartbeat
            self._heartbeat_callback,
        )
        self.status.ready()

        # --- Cached state ----------------------------------------------------
        self.path = None
        self.detected_orange_cones = []


        # --- ROS pub/sub -----------------------------------------------------
        self.subscriber1 = self.create_subscription(
            MarkerArray,
            "/perception_markers",
            self.receiveFromPerception,
            10,
        )
        self.publisher = self.create_publisher(Path, "/path", 10)
        self.time_duration = self.create_publisher(
            Float64,
            '/diagnostics/comp_time/global_planning_dl',
            10
        )

    # ── Heartbeat ────────────────────────────────────────────────────
    def _heartbeat_callback(self):
        self.status.running()

    # ── Perception & Inference Callback ──────────────────────────────
    def receiveFromPerception(self, msg: MarkerArray) -> None:
        start_time = time.perf_counter()
        orange_cones = []
        try:
            if len(msg.markers) == 0:
                return

            incoming_stamp = None
            for marker in msg.markers:
                if marker.action == marker.DELETEALL:
                    continue
                if marker.header.stamp.sec != 0 or marker.header.stamp.nanosec != 0:
                    incoming_stamp = marker.header.stamp
                    break

            if incoming_stamp is None:
                incoming_stamp = self.get_clock().now().to_msg()

            visible_cones = []

            for marker in msg.markers:
                # Local frame:  X Forward, Y Left →  Model:  X Right, Y Forward
                x_model = -marker.pose.position.y
                y_model =  marker.pose.position.x

                dist = math.hypot(x_model, y_model)

                # 15-metre radius, ignore very close cones
                if dist > 15.0 or dist < 0.5:
                    continue

                # 60-degree forward cone
                angle = math.atan2(x_model, y_model)
                if abs(angle) > (math.pi / 3):
                    continue

                r, g, b = marker.color.r, marker.color.g, marker.color.b

                is_white  = r > 0.95 and g > 0.95 and b > 0.95
                is_blue   = b > 0.80 and g < 0.45 and r < 0.45
                is_yellow = r > 0.70 and g > 0.70 and b < 0.45

                 # Identify orange cones 
                is_small_orange = r > 0.90 and 0.55 < g < 0.75 and b < 0.10
                is_large_orange = 0.40 < r < 0.60 and 0.40 < g < 0.60 and 0.40 < b < 0.60
                is_orange = is_small_orange or is_large_orange

                if is_white:
                    continue

                if is_orange:
                    orange_cones.append((dist, [x_model, y_model]))
                    continue

                if self.is_colorless:
                    if is_blue or is_yellow:
                        visible_cones.append((dist, [x_model, y_model]))
                else:
                    if is_blue:
                        visible_cones.append((dist, [x_model, y_model, 1.0, 0.0]))
                    elif is_yellow:
                        visible_cones.append((dist, [x_model, y_model, 0.0, 1.0]))

            self.detected_orange_cones = [item[1] for item in orange_cones]

            # ==========================================================
            # SAFETY OVERRIDE: ORANGE CONES OR NO CONES (EDITED SECTION)
            # ==========================================================
            is_empty = (len(visible_cones) == 0 and len(orange_cones) == 0)
            is_orange = (len(orange_cones) >= 1 and len(visible_cones) <= 2)

            if is_orange or is_empty:
                override_path = []
                
                # Much faster, no unnecessary odometry math required.
                # In the vehicle's local frame, traveling straight forward means:
                # Model X (Lateral) = 0.0, Model Y (Forward) = distance step i
                for i in range(1, 16):
                    override_path.append([0.0, float(i)])
                    
                self.path = np.array(override_path, dtype=np.float32)
                
                if len(orange_cones) >= 1:
                    self.get_logger().info("--- ORANGE CONE DETECTED: WALKING STRAIGHT IN CAR DIRECTION ---")
                else:
                    self.get_logger().warn("--- NO CONES VISIBLE: WALKING STRAIGHT IN CAR DIRECTION ---")
                
                self.publish_current_path()
                return


            # Nearest-first, max 10 cones
            visible_cones.sort(key=lambda item: item[0])
            MAX_CONES = 10
            cones_features = [c[1] for c in visible_cones[:MAX_CONES]]

            if len(cones_features) == 0:
                return  # nothing to infer on

            cones_array = np.array(cones_features, dtype=np.float32)

            # Zero-pad to MAX_CONES rows
            feature_dim = 2 if self.is_colorless else 4
            if len(cones_array) < MAX_CONES:
                pad = np.zeros((MAX_CONES - len(cones_array), feature_dim), dtype=np.float32)
                cones_array = np.concatenate([cones_array, pad], axis=0)

            # ── Synchronous Inference ────────────────────────────────────
            try:
                # predict() runs sequentially, blocking the ROS thread until finished
                result = self.model.predict(cones_array)
                # predict() returns shape (1, 15, 2);  [0] → (15, 2)
                self.path = result[0]
                # self._publish_path()
                self._publish_path(incoming_stamp)
            except Exception as e:
                self.get_logger().error(f"Error during predict: {e}")
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000.0
            self.time_duration.publish(Float64(data=duration_ms))
            
    # ── Path publisher ──────────────────────────────────────────────
    def _publish_path(self, timestamp):
        if self.path is None:
            return

        # timestamp = self.get_clock().now().to_msg()
        path_msg = Path()
        path_msg.header.stamp    = timestamp
        path_msg.header.frame_id = "zed_left_camera_frame"

        for pt in self.path:
            pose = Pose()
            # Model (X right, Y forward) → ROS local frame (X forward, Y left)
            pose.position.y = -float(pt[0])
            pose.position.x =  float(pt[1])

            ps = PoseStamped()
            ps.pose = pose
            ps.header.stamp    = timestamp
            ps.header.frame_id = "zed_left_camera_frame"
            path_msg.poses.append(ps)

        self.publisher.publish(path_msg)

    def publish_current_path(self):
        if self.path is None:
            return
            
        timestamp = self.get_clock().now().to_msg()
        path_msg = Path()
        path_msg.header.stamp = timestamp
        path_msg.header.frame_id = "Fr1A"
        
        for dataPoint in self.path:
            pose = Pose()
            # Mapping model output to ROS coordinates
            pose.position.y = -float(dataPoint[0])
            pose.position.x = float(dataPoint[1])

            pose_stamped = PoseStamped()
            pose_stamped.pose = pose
            pose_stamped.header.frame_id = "Fr1A"  
            path_msg.poses.append(pose_stamped)

        self.publisher.publish(path_msg)
        self.get_logger().info("--- FRAME END: Path Published ---\n")
        

    # ── Clean shutdown ──────────────────────────────────────────────
    def destroy_node(self):
        self.get_logger().info("Shutting down node and popping CUDA context...")
        try:
            self.cuda_context.pop()
            self.cuda_context.detach()
        except Exception as e:
            self.get_logger().warn(f"Error while cleaning up CUDA context: {e}")
        super().destroy_node()


# ────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)

    model_file = os.path.join(
        get_package_share_directory("planning_deep_learning"),
        "Completed_Models",
        "best_model_xavier.engine",
    )
    node = PlanningDlNode(model_file)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()