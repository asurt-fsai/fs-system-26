"""
RViz Test Launch — Standalone MPC testing with simulated bicycle model

Launches:
  1. bicycle_simulator     — kinematic bicycle sim (publishes /odom, /reference_path)
  2. mpc_controller_node   — MPC solver
  3. mpc_visualizer         — RViz markers for track, heading, constraints
  4. rviz2                  — RViz with pre-configured display layout

No IPG / CarMaker dependency — runs entirely in ROS 2.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('mpc_controller')
    params_dir = os.path.join(pkg_dir, 'config')
    rviz_cfg   = os.path.join(pkg_dir, 'config', 'mpc_test.rviz')
    default_track_csv = os.path.join(pkg_dir, 'config', 'track.csv')

    # ── Launch arguments ─────────────────────────────────────────────────
    control_dt_arg = DeclareLaunchArgument(
        'control_dt', default_value='0.05')
    track_csv_arg = DeclareLaunchArgument(
        'track_csv', default_value=default_track_csv,
        description='Path to track CSV file (x,y per row). Empty = generated oval.')
    track_a_arg = DeclareLaunchArgument(
        'track_a', default_value='40.0',
        description='Oval semi-major axis [m] (only used when track_csv is empty)')
    track_b_arg = DeclareLaunchArgument(
        'track_b', default_value='20.0',
        description='Oval semi-minor axis [m] (only used when track_csv is empty)')

    # ── Bicycle Simulator ────────────────────────────────────────────────
    sim_node = Node(
        package='mpc_controller',
        executable='bicycle_simulator',
        name='bicycle_simulator',
        output='screen',
        parameters=[{
            'wheelbase':       1.575,
            'sim_dt':          0.01,
            'v_max':           15.0,
            'delta_max':       0.6109,
            'track_csv_path':  LaunchConfiguration('track_csv'),
            'track_a':         LaunchConfiguration('track_a'),
            'track_b':         LaunchConfiguration('track_b'),
            'track_n':         200,
            'initial_v':       2.0,
            # When CSV is loaded, initial_x/y/theta are overridden by the
            # first waypoint in the file.  These defaults only apply for
            # the generated oval fallback.
            'initial_x':       40.0,
            'initial_y':       0.0,
            'initial_theta':   1.5708,
        }],
    )

    # ── MPC Controller ───────────────────────────────────────────────────
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
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
    )

    return LaunchDescription([
        control_dt_arg,
        track_csv_arg,
        track_a_arg,
        track_b_arg,
        sim_node,
        # Give sim 1 s to publish the track before MPC starts
        TimerAction(period=1.0, actions=[mpc_node]),
        viz_node,
        rviz_node,
    ])
