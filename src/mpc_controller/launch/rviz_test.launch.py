"""
RViz Test Launch — Standalone MPC testing with simulated bicycle model

Launches:
  1. bicycle_simulator     — kinematic bicycle sim (publishes /carmaker/Odometry, /path)
  2. mpc_controller_node   — MPC solver (remapped to talk to bicycle sim topics)
  3. mpc_visualizer         — RViz markers for track, heading, constraints
  4. rviz2                  — RViz with pre-configured display layout

No IPG / CarMaker dependency — runs entirely in ROS 2.
"""

import os
import json
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
    model_json = os.path.join(params_dir, 'model.json')

    # Read r_inner / r_outer from model.json so the visualizer uses the same
    # track boundary offsets as the MPC solver.
    r_inner = 1.5
    r_outer = 1.5
    try:
        with open(model_json) as f:
            m = json.load(f)
            r_inner = float(m.get('r_inner', r_inner))
            r_outer = float(m.get('r_outer', r_outer))
    except Exception:
        pass  # use defaults if file not found at configure time

    # ── Launch arguments ─────────────────────────────────────────────────
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
    # Topic remappings needed for bicycle-sim mode:
    #   /odom           → /carmaker/Odometry  (simulator publishes here)
    #   /ackermann_cmd  → /ackr               (simulator subscribes here)
    mpc_node = Node(
        package='mpc_controller',
        executable='mpc_controller_node',
        name='mpc_controller',
        output='screen',
        parameters=[{
            'control_frequency': 20.0,    # 20 Hz — safe for Python sim
            'model_path':        model_json,
            'costs_path':        os.path.join(params_dir, 'cost.json'),
            'bounds_path':       os.path.join(params_dir, 'bounds.json'),
            'norm_path':         os.path.join(params_dir, 'normalization.json'),
            # Bicycle sim puts steering angle in odom.twist.linear.y
            'use_odom_steering': True,
            # CSV debug log (written to /tmp/mpc_data.csv by default)
            'csv_output_path':   '/tmp/mpc_data.csv',
        }],
        remappings=[
            ('/odom',          '/carmaker/Odometry'),
            ('/ackermann_cmd', '/ackr'),
        ],
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
            'track_width':  (r_inner + r_outer) / 2.0,  # fallback symmetric width
            'r_inner':      r_inner,   # from model.json — inner boundary offset
            'r_outer':      r_outer,   # from model.json — outer boundary offset
            'cone_spacing': 5,
        }],
    )

    # ── RViz ─────────────────────────────────────────────────────────────
    # GTK_PATH must be cleared so the VS Code snap's GTK modules do not
    # inject the snap/core20 libpthread (Ubuntu 20.04) into the process,
    # which is incompatible with the system glibc and causes:
    #   "symbol lookup error: libpthread.so.0: undefined symbol __libc_pthread_init"
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
        additional_env={'GTK_PATH': ''},
    )

    return LaunchDescription([
        track_csv_arg,
        track_a_arg,
        track_b_arg,
        sim_node,
        # Give sim 1 s to publish the track before MPC starts
        TimerAction(period=1.0, actions=[mpc_node]),
        viz_node,
        rviz_node,
    ])
