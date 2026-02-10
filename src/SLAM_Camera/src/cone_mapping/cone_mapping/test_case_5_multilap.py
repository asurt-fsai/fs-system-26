#!/usr/bin/env python3
"""
Test Case 5: Multi-Lap Map Accumulation
Tests map persistence and refinement across multiple laps
"""

import rclpy
import numpy as np
from perception_simulator_base import PerceptionSimulatorBase, ConeType


class MultiLapSimulator(PerceptionSimulatorBase):
    """
    Simulates multiple laps of the same track to test:
    - Map accumulation and refinement
    - Position convergence over time
    - Landmark reuse from previous laps
    - Gradual noise reduction
    """
    
    def __init__(self):
        super().__init__('perception_sim_multilap')
        
        # Parameters that improve over laps
        self.position_noise_std = 0.12
        self.detection_probability = 0.82
        self.id_reset_probability = 0.2
        
        # Lap tracking
        self.current_lap = 0
        self.lap_start_time = 0.0
        
        # Setup track
        self.setup_track()
        
        self.get_logger().info("Test Case 5: Multi-Lap Accumulation - Initialized")
    
    def setup_track(self):
        """
        Create a realistic Formula Student autocross track.
        """
        self.ground_truth_cones = []
        
        # Start/finish straight
        for x in np.arange(0, 15, 3):
            self.ground_truth_cones.append({
                'position': np.array([x, 3.0]),
                'type': ConeType.BLUE
            })
            self.ground_truth_cones.append({
                'position': np.array([x, -3.0]),
                'type': ConeType.YELLOW
            })
        
        # First turn (90 degree right)
        for i, theta in enumerate(np.linspace(0, np.pi/2, 6)):
            r = 8.0
            x = 15 + r * np.sin(theta)
            y = -3.0 - r * (1 - np.cos(theta))
            
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.YELLOW
            })
            
            x = 15 + (r + 6.0) * np.sin(theta)
            y = -3.0 - (r + 6.0) * (1 - np.cos(theta))
            
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.BLUE
            })
        
        # Straight section 2
        for y in np.arange(-11, -30, -3):
            self.ground_truth_cones.append({
                'position': np.array([23.0, y]),
                'type': ConeType.BLUE
            })
            self.ground_truth_cones.append({
                'position': np.array([17.0, y]),
                'type': ConeType.YELLOW
            })
        
        # Second turn (180 degree hairpin)
        for i, theta in enumerate(np.linspace(0, np.pi, 10)):
            r = 5.0
            x = 20.0 + r * np.cos(theta)
            y = -30.0 + r * np.sin(theta)
            
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.YELLOW if x > 20 else ConeType.BLUE
            })
        
        # Return straight
        for y in np.arange(-28, 0, 3):
            self.ground_truth_cones.append({
                'position': np.array([11.0, y]),
                'type': ConeType.YELLOW
            })
            self.ground_truth_cones.append({
                'position': np.array([5.0, y]),
                'type': ConeType.BLUE
            })
        
        # Final turn back to start
        for i, theta in enumerate(np.linspace(-np.pi/2, 0, 6)):
            r = 6.0
            x = 8.0 + r * np.cos(theta)
            y = r * np.sin(theta)
            
            self.ground_truth_cones.append({
                'position': np.array([x, y]),
                'type': ConeType.BLUE
            })
        
        # Start/finish markers (orange)
        self.ground_truth_cones.append({
            'position': np.array([0.0, 3.5]),
            'type': ConeType.ORANGE
        })
        self.ground_truth_cones.append({
            'position': np.array([0.0, -3.5]),
            'type': ConeType.ORANGE
        })
        
        self.get_logger().info(f"Autocross track setup: {len(self.ground_truth_cones)} cones")
    
    def update_vehicle_pose(self, dt):
        """
        Follow a pre-programmed path around the track.
        """
        speed = 5.0  # Constant speed
        
        # Simple waypoint-based navigation
        x, y, theta = self.vehicle_position
        
        # Define waypoints
        if x < 15 and abs(y) < 5:
            # Straight section 1
            target_heading = 0.0
        elif x >= 15 and x < 23 and y > -15:
            # Turn 1
            target_heading = -np.pi / 2
        elif x >= 17 and x <= 23 and y < -11:
            # Straight section 2
            target_heading = -np.pi / 2
        elif x >= 15 and y < -25:
            # Hairpin
            target_heading = np.pi if x > 18 else np.pi / 2
        elif x < 15 and y < -5:
            # Return straight
            target_heading = np.pi / 2
        else:
            # Final turn
            target_heading = 0.0
        
        # Smooth steering
        heading_error = self.normalize_angle(target_heading - theta)
        self.vehicle_position[2] += np.clip(heading_error * 2.0 * dt, -0.8*dt, 0.8*dt)
        
        # Update position
        self.vehicle_position[0] += speed * dt * np.cos(self.vehicle_position[2])
        self.vehicle_position[1] += speed * dt * np.sin(self.vehicle_position[2])
        
        # Check for lap completion
        if x > -2 and x < 2 and abs(y) < 2 and (self.time_elapsed - self.lap_start_time) > 5.0:
            self.current_lap += 1
            self.lap_start_time = self.time_elapsed
            
            # Improve detection quality with each lap (simulating adaptation)
            self.position_noise_std = max(0.03, self.position_noise_std * 0.9)
            self.detection_probability = min(0.95, self.detection_probability + 0.03)
            self.id_reset_probability = max(0.05, self.id_reset_probability * 0.8)
            
            self.get_logger().info(
                f"LAP {self.current_lap} COMPLETE - "
                f"Noise: {self.position_noise_std:.3f}, "
                f"Detection: {self.detection_probability:.2f}"
            )
        
        # Don't reset position - continuous lapping


def main(args=None):
    rclpy.init(args=args)
    
    simulator = MultiLapSimulator()
    
    try:
        rclpy.spin(simulator)
    except KeyboardInterrupt:
        pass
    finally:
        simulator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
