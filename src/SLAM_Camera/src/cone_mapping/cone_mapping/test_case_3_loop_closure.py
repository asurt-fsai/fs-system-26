#!/usr/bin/env python3
"""
Test Case 3: Loop Closure Test
Circular track with simulated SLAM drift and loop closure events
"""

import rclpy
import numpy as np
from perception_simulator_base import PerceptionSimulatorBase, ConeType


class LoopClosureSimulator(PerceptionSimulatorBase):
    """
    Simulates a closed-loop track with SLAM drift accumulation
    and periodic loop closure corrections.
    
    Tests the system's ability to handle:
    - Accumulated drift before loop closure
    - Sudden pose corrections during loop closure
    - Map consistency across multiple laps
    """
    
    def __init__(self):
        super().__init__('perception_sim_loop_closure')
        
        # Moderate noise
        self.position_noise_std = 0.08
        self.detection_probability = 0.88
        self.id_reset_probability = 0.15
        
        # SLAM simulation parameters
        self.drift_rate = 0.02  # meters per second of accumulated error
        self.accumulated_drift = np.array([0.0, 0.0])
        self.last_loop_closure_position = np.array([0.0, 0.0])
        self.loop_closure_threshold = 40.0  # meters traveled before loop closure
        self.distance_traveled = 0.0
        
        # Setup track
        self.setup_track()
        
        self.get_logger().info("Test Case 3: Loop Closure - Initialized")
    
    def setup_track(self):
        """
        Create a circular track.
        """
        self.ground_truth_cones = []
        
        # Circular track parameters
        radius_inner = 8.0  # Yellow cones
        radius_outer = 12.0  # Blue cones
        num_cones = 24
        
        for i in range(num_cones):
            angle = 2 * np.pi * i / num_cones
            
            # Inner (yellow) cones
            x_inner = radius_inner * np.cos(angle)
            y_inner = radius_inner * np.sin(angle)
            self.ground_truth_cones.append({
                'position': np.array([x_inner, y_inner]),
                'type': ConeType.YELLOW
            })
            
            # Outer (blue) cones
            x_outer = radius_outer * np.cos(angle)
            y_outer = radius_outer * np.sin(angle)
            self.ground_truth_cones.append({
                'position': np.array([x_outer, y_outer]),
                'type': ConeType.BLUE
            })
        
        # Add start/finish line markers (orange)
        self.ground_truth_cones.append({
            'position': np.array([radius_outer, 0.0]),
            'type': ConeType.ORANGE
        })
        self.ground_truth_cones.append({
            'position': np.array([radius_inner, 0.0]),
            'type': ConeType.ORANGE
        })
        
        self.get_logger().info(f"Circular track setup: {len(self.ground_truth_cones)} cones")
    
    def publish_pose(self):
        """
        Override to add simulated SLAM drift and loop closures.
        """
        # Add accumulated drift to pose
        drifted_position = self.vehicle_position.copy()
        drifted_position[0] += self.accumulated_drift[0]
        drifted_position[1] += self.accumulated_drift[1]
        
        # Create pose message with drift
        from geometry_msgs.msg import PoseStamped
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = 'map'
        
        pose_msg.pose.position.x = drifted_position[0]
        pose_msg.pose.position.y = drifted_position[1]
        pose_msg.pose.position.z = 0.0
        
        theta = drifted_position[2]
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = np.sin(theta / 2)
        pose_msg.pose.orientation.w = np.cos(theta / 2)
        
        self.pose_pub.publish(pose_msg)
    
    def update_vehicle_pose(self, dt):
        """
        Drive around the circular track with simulated drift.
        """
        speed = 6.0  # m/s
        radius = 10.0  # Follow middle of track
        
        # Angular velocity for circular motion
        omega = speed / radius
        
        # Update heading
        self.vehicle_position[2] += omega * dt
        self.vehicle_position[2] = self.normalize_angle(self.vehicle_position[2])
        
        # Update position (circular motion)
        self.vehicle_position[0] = radius * np.cos(self.vehicle_position[2] + np.pi/2)
        self.vehicle_position[1] = radius * np.sin(self.vehicle_position[2] + np.pi/2)
        
        # Accumulate drift (random walk)
        drift_increment = np.random.randn(2) * self.drift_rate * dt
        self.accumulated_drift += drift_increment
        
        # Track distance traveled
        self.distance_traveled += speed * dt
        
        # Check for loop closure event
        current_pos = np.array([self.vehicle_position[0], self.vehicle_position[1]])
        distance_from_start = np.linalg.norm(current_pos - self.last_loop_closure_position)
        
        if self.distance_traveled > self.loop_closure_threshold and distance_from_start < 3.0:
            # Loop closure detected!
            self.get_logger().info(
                f"LOOP CLOSURE EVENT - Correcting drift of "
                f"({self.accumulated_drift[0]:.2f}, {self.accumulated_drift[1]:.2f})m"
            )
            
            # Reset drift (simulate loop closure correction)
            self.accumulated_drift = np.array([0.0, 0.0])
            self.last_loop_closure_position = current_pos.copy()
            self.distance_traveled = 0.0


def main(args=None):
    rclpy.init(args=args)
    
    simulator = LoopClosureSimulator()
    
    try:
        rclpy.spin(simulator)
    except KeyboardInterrupt:
        pass
    finally:
        simulator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
