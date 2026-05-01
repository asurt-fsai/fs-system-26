"""
MPC Controller Launch — External simulator integration

Launches:
  1. mpc_controller_node   — MPC solver (subscribes to /path, /odom, publishes to /action)
  2. mpc_visualizer        — RViz markers for track, heading, constraints
  3. rviz2                 — RViz with pre-configured display layout (optional)

Expects external system to provide:
  - /path         : nav_msgs/Path — reference trajectory (publish once or periodically)
  - /odom         : nav_msgs/Odometry — vehicle state feedback

The controller publishes to:
  - /action       : ackermann_msgs/AckermannDriveStamped — steering angle & acceleration commands
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('mpc_controller')
    params_dir = os.path.join(pkg_dir, 'config')
    rviz_cfg   = os.path.join(pkg_dir, 'config', 'mpc_test.rviz')

    # ── Launch arguments ─────────────────────────────────────────────────
    control_dt_arg = DeclareLaunchArgument(
        'control_dt', default_value='0.05',
        description='MPC control loop period [s]')
    
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Launch RViz for visualization')

    # ── MPC Controller ───────────────────────────────────────────────────
    # Subscribes to:
    #   /path  — reference trajectory (nav_msgs/Path)
    #   /odom  — odometry feedback (nav_msgs/Odometry)
    # Publishes to:
    #   /action — control commands (ackermann_msgs/AckermannDriveStamped)
    mpc_node = Node(
        package='mpc_controller',
        executable='mpc_controller_node',
        name='mpc_controller',
        output='screen',
        parameters=[{
            'control_dt':  LaunchConfiguration('control_dt'),
            'model_path':  os.path.join(params_dir, 'model.json'),
            'costs_path':  os.path.join(params_dir, 'cost.json'),
            'bounds_path': os.path.join(params_dir, 'bounds.json'),
            'norm_path':   os.path.join(params_dir, 'normalization.json'),
        }],
    )

    # ── MPC Visualizer ───────────────────────────────────────────────────
    # Publishes RViz markers for visualization
    viz_node = Node(
        package='mpc_controller',
        executable='mpc_visualizer',
        name='mpc_visualizer',
        output='screen',
        parameters=[{
            'car_length':   2.8,
            'car_width':    1.4,
            'wheelbase':    1.575,
            'track_width':  1.5,
            'cone_spacing': 5,
        }],
    )

    # ── RViz ─────────────────────────────────────────────────────────────
    # Import for conditional launching
    from launch.conditions import IfCondition

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([
        control_dt_arg,
        use_rviz_arg,
        mpc_node,
        viz_node,
        rviz_node,
    ])
