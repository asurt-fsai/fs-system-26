"""
IPG Launch File (Absolute Paths) — MPC Controller for the real car (IPG / CarMaker)

This is a workaround version that uses absolute paths instead of relying on
package resource discovery. This allows launching even if ROS 2 can't find the package.

Launches:
  1. mpc_controller_node   — subscribes /odom + /reference_path → publishes /cmd_vel
  2. mpc_visualizer         — publishes RViz markers for track, heading, constraints

Topics expected from IPG bridge:
  /odom             (nav_msgs/Odometry)    — vehicle state
  /reference_path   (nav_msgs/Path)        — track waypoints

Topics published:
  /cmd_vel                  (geometry_msgs/Twist)   — [accel, steering_rate]
  /mpc/predicted_path       (nav_msgs/Path)         — MPC horizon trajectory
  /mpc/track_markers        (visualization_msgs/MarkerArray)
  /mpc/heading_arrow        (visualization_msgs/Marker)
  /mpc/constraint_markers   (visualization_msgs/MarkerArray)
  /mpc/vehicle_footprint    (visualization_msgs/Marker)
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Absolute paths - adjust based on workspace location
WORKSPACE_ROOT = "/home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26"
INSTALL_ROOT = os.path.join(WORKSPACE_ROOT, "install")
CONFIG_DIR = os.path.join(INSTALL_ROOT, "mpc_controller", "share", "mpc_controller", "config")


def generate_launch_description():
    # ── Launch arguments ─────────────────────────────────────────────────
    control_dt_arg = DeclareLaunchArgument(
        'control_dt', default_value='0.05',
        description='MPC control loop period [s]')

    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value=os.path.join(CONFIG_DIR, 'model.json'),
        description='Path to model.json')

    costs_path_arg = DeclareLaunchArgument(
        'costs_path',
        default_value=os.path.join(CONFIG_DIR, 'cost.json'),
        description='Path to cost.json')

    bounds_path_arg = DeclareLaunchArgument(
        'bounds_path',
        default_value=os.path.join(CONFIG_DIR, 'bounds.json'),
        description='Path to bounds.json')

    norm_path_arg = DeclareLaunchArgument(
        'norm_path',
        default_value=os.path.join(CONFIG_DIR, 'normalization.json'),
        description='Path to normalization.json')

    # ── MPC Controller Node ──────────────────────────────────────────────
    mpc_node = Node(
        package='mpc_controller',
        executable='mpc_controller_node',
        name='mpc_controller',
        output='screen',
        parameters=[{
            'control_dt':  LaunchConfiguration('control_dt'),
            'model_path':  LaunchConfiguration('model_path'),
            'costs_path':  LaunchConfiguration('costs_path'),
            'bounds_path': LaunchConfiguration('bounds_path'),
            'norm_path':   LaunchConfiguration('norm_path'),
        }],
    )

    # ── MPC Visualizer Node ──────────────────────────────────────────────
    viz_node = Node(
        package='mpc_controller',
        executable='mpc_visualizer',
        name='mpc_visualizer',
        output='screen',
        parameters=[{
            'car_length':  3.0,
            'car_width':   1.5,
            'track_width': 3.0,
        }],
    )

    return LaunchDescription([
        control_dt_arg,
        model_path_arg,
        costs_path_arg,
        bounds_path_arg,
        norm_path_arg,
        mpc_node,
        viz_node,
    ])
