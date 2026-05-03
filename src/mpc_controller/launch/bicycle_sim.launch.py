"""
bicycle_sim.launch.py — Standalone bicycle simulator

Launches ONLY the bicycle simulator node.
It will:
  • Load the track from the CSV file (track_csv parameter)
  • Publish the track on /path (transient_local, replays for late subscribers)
  • Publish vehicle odometry on /carmaker/Odometry
  • Subscribe to Ackermann commands on /ackr

Run:
  ros2 launch mpc_controller bicycle_sim.launch.py
  ros2 launch mpc_controller bicycle_sim.launch.py track_csv:=/path/to/track.csv
"""

import os
import json
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('mpc_controller')
    cfg_dir = os.path.join(pkg_dir, 'config')

    # Load node/topic names from nodes.json
    nodes_cfg = {'node_names': {'bicycle_simulator': 'bicycle_simulator'},
                 'topics': {'ackermann_cmd': '/ackr',
                            'odometry': '/carmaker/Odometry',
                            'reference_path': '/path'}}
    try:
        with open(os.path.join(cfg_dir, 'nodes.json')) as f:
            nodes_cfg = json.load(f)
    except Exception:
        pass

    node_name   = nodes_cfg['node_names']['bicycle_simulator']
    topic_ackr  = nodes_cfg['topics']['ackermann_cmd']
    topic_odom  = nodes_cfg['topics']['odometry']
    topic_path  = nodes_cfg['topics']['reference_path']

    default_track = os.path.join(cfg_dir, 'track.csv')

    track_csv_arg = DeclareLaunchArgument(
        'track_csv', default_value=default_track,
        description='Path to track centerline CSV (x,y per row). '
                    'Leave empty to use generated oval.')
    initial_v_arg = DeclareLaunchArgument(
        'initial_v', default_value='2.0',
        description='Initial vehicle speed [m/s]')

    sim_node = Node(
        package='mpc_controller',
        executable='bicycle_simulator',
        name=node_name,
        output='screen',
        parameters=[{
            'wheelbase':      1.575,
            'sim_dt':         0.01,
            'v_max':          15.0,
            'delta_max':      0.6109,
            'track_csv_path': LaunchConfiguration('track_csv'),
            'initial_v':      LaunchConfiguration('initial_v'),
        }],
        remappings=[
            ('/ackr',              topic_ackr),
            ('/carmaker/Odometry', topic_odom),
            ('/path',              topic_path),
        ],
    )

    return LaunchDescription([
        track_csv_arg,
        initial_v_arg,
        sim_node,
    ])
