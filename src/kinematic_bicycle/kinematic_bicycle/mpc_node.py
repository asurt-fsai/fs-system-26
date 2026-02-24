"""MPC Controller ROS 2 Node

Wraps MPC solver with ROS 2 interface
"""

import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import Float32MultiArray
import tf_transformations

from .mpc import MPCConfig, MPCSolver
from .mpc.utils import wrap_angle


class MPCControllerNode(Node):
    """ROS 2 node for MPC-based vehicle control"""
    
    def __init__(self):
        super().__init__('mpc_controller')
        self.get_logger().info('MPC Controller Node initialized')
        
        # Configuration
        self.config = MPCConfig(
            horizon=10,
            dt=0.1,
            wheelbase=2.5,
            v_max=2.0,
            v_min=-1.0
        )
        
        # MPC Solver
        self.mpc_solver = MPCSolver(self.config)
        
        # State tracking
        self.current_state = np.array([0.0, 0.0, 0.0, 0.0])  # [x, y, theta, delta]
        self.reference_path = None
        self.reference_index = 0
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.predicted_path_pub = self.create_publisher(Path, '/mpc/predicted_path', 10)
        self.control_debug_pub = self.create_publisher(Float32MultiArray, '/mpc/debug', 10)
        
        # Subscribers
        self.state_sub = self.create_subscription(
            Odometry, '/odom', self._odom_callback, 10
        )
        self.reference_path_sub = self.create_subscription(
            Path, '/reference_path', self._path_callback, 10
        )
        
        # Timer for control loop
        self.control_timer = self.create_timer(self.config.dt, self._control_loop)
    
    def _odom_callback(self, msg: Odometry):
        """Update current state from odometry
        
        Args:
            msg: Odometry message
        """
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        
        # Extract heading from quaternion
        _, _, theta = tf_transformations.euler_from_quaternion(
            [ori.x, ori.y, ori.z, ori.w]
        )
        
        # State: [x, y, theta, delta] (delta=0 for now, can estimate from steering)
        self.current_state = np.array([pos.x, pos.y, theta, 0.0])
    
    def _path_callback(self, msg: Path):
        """Update reference path
        
        Args:
            msg: Path message
        """
        if len(msg.poses) > 0:
            # Convert Path to reference trajectory
            self.reference_path = msg
            self.reference_index = 0
    
    def _get_reference_trajectory(self) -> np.ndarray:
        """Extract reference trajectory for MPC
        
        Returns:
            reference_traj: (horizon+1, 4) reference states
        """
        if self.reference_path is None:
            # Default: stay at current position
            return np.tile(self.current_state, (self.config.horizon + 1, 1))
        
        reference_traj = np.zeros((self.config.horizon + 1, 4))
        
        for i in range(self.config.horizon + 1):
            idx = min(
                self.reference_index + i,
                len(self.reference_path.poses) - 1
            )
            pose = self.reference_path.poses[idx].pose
            pos = pose.position
            ori = pose.orientation
            
            _, _, theta = tf_transformations.euler_from_quaternion(
                [ori.x, ori.y, ori.z, ori.w]
            )
            
            reference_traj[i] = np.array([pos.x, pos.y, theta, 0.0])
        
        return reference_traj
    
    def _control_loop(self):
        """Main control loop - runs at dt Hz"""
        if self.reference_path is None:
            return
        
        # Get reference trajectory for this control step
        reference_traj = self._get_reference_trajectory()
        
        # Solve MPC
        try:
            optimal_control, predicted_traj, info = self.mpc_solver.solve(
                self.current_state,
                reference_traj
            )
            
            # Get first control from sequence
            v, delta_dot = optimal_control[0]
            
            # Publish control command
            twist = Twist()
            twist.linear.x = float(v)
            twist.angular.z = float(delta_dot)
            self.cmd_vel_pub.publish(twist)
            
            # Publish predicted trajectory for visualization
            self._publish_predicted_path(predicted_traj)
            
            # Debug info
            self._publish_debug_info(info)
            
            # Update reference index (look-ahead)
            if self.reference_index < len(self.reference_path.poses) - 1:
                self.reference_index += 1
            
        except Exception as e:
            self.get_logger().error(f'MPC solve failed: {e}')
    
    def _publish_predicted_path(self, trajectory: np.ndarray):
        """Publish predicted trajectory as Path message
        
        Args:
            trajectory: Predicted trajectory (N+1, 4)
        """
        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()
        
        for state in trajectory:
            pose_stamped = PoseStamped()
            pose_stamped.header = path_msg.header
            
            pose_stamped.pose.position.x = float(state[0])
            pose_stamped.pose.position.y = float(state[1])
            
            # Convert heading to quaternion
            quat = tf_transformations.quaternion_from_euler(0, 0, state[2])
            pose_stamped.pose.orientation.x = quat[0]
            pose_stamped.pose.orientation.y = quat[1]
            pose_stamped.pose.orientation.z = quat[2]
            pose_stamped.pose.orientation.w = quat[3]
            
            path_msg.poses.append(pose_stamped)
        
        self.predicted_path_pub.publish(path_msg)
    
    def _publish_debug_info(self, info: dict):
        """Publish debug information
        
        Args:
            info: Solver info dictionary
        """
        debug_msg = Float32MultiArray()
        debug_msg.data = [
            float(info.get('function_value', 0.0)),
            float(info.get('iterations', 0)),
            1.0 if info.get('success', False) else 0.0
        ]
        self.control_debug_pub.publish(debug_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MPCControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
