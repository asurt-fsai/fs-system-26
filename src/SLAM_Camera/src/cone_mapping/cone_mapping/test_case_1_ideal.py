#!/usr/bin/env python3
"""
Test Case 1: Ideal Conditions
Clean detection on a straight track with minimal noise
"""

import rclpy
import numpy as np
from perception_simulator_base import PerceptionSimulatorBase, ConeType


class IdealConditionsSimulator(PerceptionSimulatorBase):
    """
    Simulates ideal perception conditions:
    - Straight track
    - Low noise
    - High detection probability
    - Stable tracking IDs
    """
    
    def __init__(self):
        super().__init__('perception_sim_ideal')
        
        # Ideal parameters
        self.position_noise_std = 0.02  # Very low noise
        self.detection_probability = 0.98  # High detection rate
        self.id_reset_probability = 0.01  # Very stable IDs
        
        # Setup track
        self.setup_track()
        
        self.get_logger().info("Test Case 1: Ideal Conditions - Initialized")
    
    def setup_track(self):
        """
        Create a straight track with regularly spaced cones.
        
        Track layout:
        Blue cones on left (y = 3m)
        Yellow cones on right (y = -3m)
        50 meters long
        """
        self.ground_truth_cones = []
        
        # Straight track: 50 meters, cones every 5 meters
        for x in np.arange(0, 50, 5):
            # Blue cone on left
            self.ground_truth_cones.append({
                'position': np.array([x, 3.0]),
                'type': ConeType.BLUE
            })
            
            # Yellow cone on right
            self.ground_truth_cones.append({
                'position': np.array([x, -3.0]),
                'type': ConeType.YELLOW
            })
        
        self.get_logger().info(f"Track setup: {len(self.ground_truth_cones)} cones")
    
    def update_vehicle_pose(self, dt):
        """
        Drive straight down the track at constant speed.
        
        Args:
            dt: Time step in seconds
        """
        speed = 5.0  # m/s (18 km/h)
        
        # Move forward
        self.vehicle_position[0] += speed * dt * np.cos(self.vehicle_position[2])
        self.vehicle_position[1] += speed * dt * np.sin(self.vehicle_position[2])
        
        # Keep heading straight
        self.vehicle_position[2] = 0.0
        
        # Loop back to start after reaching end
        if self.vehicle_position[0] > 55:
            self.vehicle_position[0] = -5.0
            self.vehicle_position[1] = 0.0
            self.vehicle_position[2] = 0.0
            self.get_logger().info("Lap complete - resetting to start")


def main(args=None):
    rclpy.init(args=args)
    
    simulator = IdealConditionsSimulator()
    
    try:
        rclpy.spin(simulator)
    except KeyboardInterrupt:
        pass
    finally:
        simulator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
