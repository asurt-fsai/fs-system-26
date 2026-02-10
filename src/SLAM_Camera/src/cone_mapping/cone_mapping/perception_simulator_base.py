#!/usr/bin/env python3
"""
Perception Simulator - Base Class
Simulates the perception system publishing cone detections
"""

import rclpy
from rclpy.node import Node
import numpy as np
from geometry_msgs.msg import Point, PoseStamped, Pose, Quaternion
from std_msgs.msg import Header

try:
    from cone_mapping.msg import Landmark, LandmarkArray
except ImportError:
    print("Warning: Using placeholder messages")
    from dataclasses import dataclass
    
    @dataclass
    class Point:
        x: float = 0.0
        y: float = 0.0
        z: float = 0.0
    
    @dataclass
    class Landmark:
        position: Point = None
        type: int = 0
        identifier: int = 0
        probability: float = 0.0
        
        def __post_init__(self):
            if self.position is None:
                self.position = Point()
    
    @dataclass
    class LandmarkArray:
        header: Header = None
        landmarks: list = None
        
        def __post_init__(self):
            if self.header is None:
                self.header = Header()
            if self.landmarks is None:
                self.landmarks = []


class ConeType:
    """Cone type enumeration"""
    BLUE = 0
    YELLOW = 1
    ORANGE = 2
    UNKNOWN = 3


class PerceptionSimulatorBase(Node):
    """
    Base class for perception simulation.
    Simulates a stereo camera detecting cones in the environment.
    """
    
    def __init__(self, node_name='perception_simulator'):
        super().__init__(node_name)
        
        # Publishers
        self.landmark_pub = self.create_publisher(
            LandmarkArray,
            '/perception/landmarks',
            10
        )
        
        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/zed2i/zed_node/pose',
            10
        )
        
        # Simulation state
        self.vehicle_position = np.array([0.0, 0.0, 0.0])  # x, y, theta
        self.time_elapsed = 0.0
        
        # Ground truth cone positions (world frame)
        self.ground_truth_cones = []
        
        # Camera parameters
        self.max_detection_range = 20.0  # meters
        self.fov_angle = np.deg2rad(120)  # degrees to radians
        self.camera_offset = np.array([0.3, 0.0, 0.5])  # x, y, z from base_link
        
        # Noise parameters (can be overridden by subclasses)
        self.position_noise_std = 0.05  # meters
        self.detection_probability = 0.95
        
        # Tracking ID management (intentionally unstable as per spec)
        self.next_id = 0
        self.cone_id_map = {}  # Maps cone index to current ID
        self.id_reset_probability = 0.1  # Probability of ID reset per frame
        
        # Simulation timer (10 Hz)
        self.timer = self.create_timer(0.1, self.simulation_step)
        
        self.get_logger().info(f"{node_name} initialized")
    
    def setup_track(self):
        """
        Setup ground truth cone positions.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement setup_track()")
    
    def update_vehicle_pose(self, dt):
        """
        Update vehicle position and orientation.
        Must be implemented by subclasses.
        
        Args:
            dt: Time step in seconds
        """
        raise NotImplementedError("Subclasses must implement update_vehicle_pose()")
    
    def simulation_step(self):
        """Main simulation loop executed at 10 Hz"""
        dt = 0.1  # 10 Hz
        self.time_elapsed += dt
        
        # Update vehicle motion
        self.update_vehicle_pose(dt)
        
        # Publish vehicle pose
        self.publish_pose()
        
        # Detect visible cones
        visible_cones = self.detect_visible_cones()
        
        # Add noise and convert to detections
        detections = self.generate_detections(visible_cones)
        
        # Publish detections
        self.publish_detections(detections)
    
    def publish_pose(self):
        """Publish current vehicle pose in map frame"""
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = 'map'
        
        # Position
        pose_msg.pose.position.x = self.vehicle_position[0]
        pose_msg.pose.position.y = self.vehicle_position[1]
        pose_msg.pose.position.z = 0.0
        
        # Orientation (yaw to quaternion)
        theta = self.vehicle_position[2]
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = np.sin(theta / 2)
        pose_msg.pose.orientation.w = np.cos(theta / 2)
        
        self.pose_pub.publish(pose_msg)
    
    def detect_visible_cones(self):
        """
        Detect cones visible from current vehicle position.
        
        Returns:
            List of dicts: [{'index': int, 'position': np.array, 'type': int, 'distance': float}, ...]
        """
        visible = []
        
        x, y, theta = self.vehicle_position
        
        # Camera position in world frame
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        
        camera_world = np.array([
            x + self.camera_offset[0] * cos_theta,
            y + self.camera_offset[0] * sin_theta
        ])
        
        for idx, cone in enumerate(self.ground_truth_cones):
            cone_pos = cone['position']
            cone_type = cone['type']
            
            # Vector from camera to cone
            to_cone = cone_pos - camera_world
            distance = np.linalg.norm(to_cone)
            
            # Distance check
            if distance > self.max_detection_range:
                continue
            
            # Field of view check
            cone_angle = np.arctan2(to_cone[1], to_cone[0])
            angle_diff = self.normalize_angle(cone_angle - theta)
            
            if abs(angle_diff) > self.fov_angle / 2:
                continue
            
            # Random detection failures
            if np.random.rand() > self.detection_probability:
                continue
            
            visible.append({
                'index': idx,
                'position': cone_pos.copy(),
                'type': cone_type,
                'distance': distance
            })
        
        return visible
    
    def generate_detections(self, visible_cones):
        """
        Generate noisy detections from visible cones.
        
        Args:
            visible_cones: List of visible cone dicts
            
        Returns:
            List of Landmark messages in camera frame
        """
        detections = []
        
        x, y, theta = self.vehicle_position
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        
        for cone in visible_cones:
            idx = cone['index']
            world_pos = cone['position']
            cone_type = cone['type']
            distance = cone['distance']
            
            # Transform to vehicle frame
            dx = world_pos[0] - x
            dy = world_pos[1] - y
            
            vehicle_x = dx * cos_theta + dy * sin_theta
            vehicle_y = -dx * sin_theta + dy * cos_theta
            
            # Transform to camera frame (camera is offset forward)
            camera_x = vehicle_x - self.camera_offset[0]
            camera_y = vehicle_y
            camera_z = self.camera_offset[2]  # Height of cone relative to camera
            
            # Add distance-dependent noise
            noise_std = self.position_noise_std * (1.0 + 0.1 * distance)
            camera_x += np.random.randn() * noise_std
            camera_y += np.random.randn() * noise_std
            camera_z += np.random.randn() * (noise_std * 0.5)
            
            # Generate or retrieve tracking ID (unstable as per spec)
            if idx not in self.cone_id_map or np.random.rand() < self.id_reset_probability:
                self.cone_id_map[idx] = self.next_id
                self.next_id += 1
            
            tracking_id = self.cone_id_map[idx]
            
            # Create detection
            landmark = Landmark()
            landmark.position = Point()
            landmark.position.x = float(camera_x)
            landmark.position.y = float(camera_y)
            landmark.position.z = float(camera_z)
            landmark.type = cone_type
            landmark.identifier = tracking_id
            landmark.probability = float(np.random.uniform(0.7, 0.99))
            
            detections.append(landmark)
        
        return detections
    
    def publish_detections(self, detections):
        """Publish landmark array"""
        msg = LandmarkArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'zed_camera'
        msg.landmarks = detections
        
        self.landmark_pub.publish(msg)
        
        if len(detections) > 0:
            self.get_logger().debug(f"Published {len(detections)} detections")
    
    @staticmethod
    def normalize_angle(angle):
        """Normalize angle to [-pi, pi]"""
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle
