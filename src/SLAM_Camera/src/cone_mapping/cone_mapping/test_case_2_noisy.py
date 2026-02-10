#!/usr/bin/env python3
"""
Test Case 2: Noisy Detections
High measurement noise and intermittent detection failures
"""

import rclpy
import numpy as np
from perception_simulator_base import PerceptionSimulatorBase, ConeType


class NoisyDetectionsSimulator(PerceptionSimulatorBase):
    """
    Simulates challenging perception conditions:
    - High position noise
    - Lower detection probability (occlusions)
    - Frequent ID resets
    - Some false color classifications
    """
    
    def __init__(self):
        super().__init__('perception_sim_noisy')
        
        # Noisy parameters
        self.position_noise_std = 0.15  # High noise (15cm base)
        self.detection_probability = 0.75  # 25% miss rate
        self.id_reset_probability = 0.3  # Very unstable IDs
        self.color_error_probability = 0.05  # 5% color misclassification
        
        # Setup track
        self.setup_track()
        
        self.get_logger().info("Test Case 2: Noisy Detections - Initialized")
    
    def setup_track(self):
        """
        Create a curved track (chicane) with varying cone spacing.
        """
        self.ground_truth_cones = []
        
        # Chicane track with varying width
        # First straight section
        for x in np.arange(0, 20, 4):
            self.ground_truth_cones.append({
                'position': np.array([x, 3.0]),
                'type': ConeType.BLUE
            })
            self.ground_truth_cones.append({
                'position': np.array([x, -3.0]),
                'type': ConeType.YELLOW
            })
        
        # Left turn
        for i, theta in enumerate(np.linspace(0, np.pi/2, 8)):
            r = 10.0
            x = 20 + r * np.sin(theta)
            y = 3.0 + r * (1 - np.cos(theta))
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.BLUE
            })
            
            x = 20 + r * np.sin(theta)
            y = -3.0 + r * (1 - np.cos(theta))
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.YELLOW
            })
        
        # Right turn back
        for i, theta in enumerate(np.linspace(0, np.pi/2, 8)):
            r = 10.0
            x = 30 + r * (1 - np.cos(theta))
            y = 13.0 - r * np.sin(theta)
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.BLUE
            })
            
            x = 30 + r * (1 - np.cos(theta))
            y = 7.0 - r * np.sin(theta)
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.YELLOW
            })
        
        # Final straight
        for x in np.arange(40, 60, 4):
            self.ground_truth_cones.append({
                'position': np.array([x, 3.0]),
                'type': ConeType.BLUE
            })
            self.ground_truth_cones.append({
                'position': np.array([x, -3.0]),
                'type': ConeType.YELLOW
            })
        
        self.get_logger().info(f"Chicane track setup: {len(self.ground_truth_cones)} cones")
    
    def generate_detections(self, visible_cones):
        """
        Override to add color classification errors.
        """
        detections = super().generate_detections(visible_cones)
        
        # Add random color errors
        for detection in detections:
            if np.random.rand() < self.color_error_probability:
                # Swap blue and yellow
                if detection.type == ConeType.BLUE:
                    detection.type = ConeType.YELLOW
                elif detection.type == ConeType.YELLOW:
                    detection.type = ConeType.BLUE
        
        return detections
    
    def update_vehicle_pose(self, dt):
        """
        Follow the chicane track with varying speed.
        """
        # Vary speed based on track section
        if self.vehicle_position[0] < 20:
            speed = 8.0  # Fast on straight
        elif self.vehicle_position[0] < 40:
            speed = 4.0  # Slow through chicane
        else:
            speed = 8.0  # Fast again
        
        # Simple path following (follows centerline)
        if self.vehicle_position[0] < 20:
            # Straight
            target_heading = 0.0
        elif self.vehicle_position[0] < 30:
            # Left turn
            target_heading = np.pi / 6
        elif self.vehicle_position[0] < 40:
            # Right turn
            target_heading = -np.pi / 6
        else:
            # Straight
            target_heading = 0.0
        
        # Smooth heading change
        heading_error = self.normalize_angle(target_heading - self.vehicle_position[2])
        self.vehicle_position[2] += np.clip(heading_error * 2.0 * dt, -0.5*dt, 0.5*dt)
        
        # Update position
        self.vehicle_position[0] += speed * dt * np.cos(self.vehicle_position[2])
        self.vehicle_position[1] += speed * dt * np.sin(self.vehicle_position[2])
        
        # Loop back
        if self.vehicle_position[0] > 65:
            self.vehicle_position[0] = -5.0
            self.vehicle_position[1] = 0.0
            self.vehicle_position[2] = 0.0
            self.get_logger().info("Lap complete - resetting to start")


def main(args=None):
    rclpy.init(args=args)
    
    simulator = NoisyDetectionsSimulator()
    
    try:
        rclpy.spin(simulator)
    except KeyboardInterrupt:
        pass
    finally:
        simulator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
