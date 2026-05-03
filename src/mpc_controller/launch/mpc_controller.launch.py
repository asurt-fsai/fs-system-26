"""
mpc_controller.launch.py — Real car / IPG CarMaker launch

Launches ONLY the MPC controller node.
Expects external system (IPG / Isaac Sim / real car) to publish:
  - /carmaker/Odometry  (nav_msgs/Odometry)  — vehicle state
  - /path               (nav_msgs/Path)       — track centerline (once, transient_local)

The controller publishes:
  - /ackr               (AckermannDriveStamped) — steering + speed commands
  - /mpc/predicted_path (nav_msgs/Path)          — MPC horizon for visualizer

Run:
  ros2 launch mpc_controller mpc_controller.launch.py
  ros2 launch mpc_controller mpc_controller.launch.py csv_enabled:=false
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

    # ── Load nodes.json ──────────────────────────────────────────────────
    nodes_cfg = {'node_names': {'mpc_controller': 'mpc_controller'},
                 'topics': {'odometry': '/carmaker/Odometry',
                            'ackermann_cmd': '/ackr',
                            'reference_path': '/path',
                            'joint_states': '/joint_states'}}
    try:
        with open(os.path.join(cfg_dir, 'nodes.json')) as f:
            nodes_cfg = json.load(f)
    except Exception:
        pass

    node_name   = nodes_cfg['node_names']['mpc_controller']
    topic_odom  = nodes_cfg['topics']['odometry']
    topic_ackr  = nodes_cfg['topics']['ackermann_cmd']
    topic_path  = nodes_cfg['topics']['reference_path']
    topic_js    = nodes_cfg['topics']['joint_states']

    # Workspace root = 4 directories up from share/mpc_controller/ (use pkg_dir, not cfg_dir)
    ws_root    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pkg_dir))))
    lap_dir    = os.path.join(ws_root, 'lap_tests')

    csv_arg = DeclareLaunchArgument(
        'csv_enabled', default_value='true',
        description='Enable lap CSV logging (true/false)')

    use_odom_steering_arg = DeclareLaunchArgument(
        'use_odom_steering', default_value='true',
        description='True = read steering from odom.twist.linear.y (bicycle_sim); '
                    'False = read from /joint_states (real car / IPG)')

    mpc_node = Node(
        package='mpc_controller',
        executable='mpc_controller_node',
        name=node_name,
        output='screen',
        parameters=[{
            'model_path':         os.path.join(cfg_dir, 'model.json'),
            'costs_path':         os.path.join(cfg_dir, 'cost.json'),
            'bounds_path':        os.path.join(cfg_dir, 'bounds.json'),
            'norm_path':          os.path.join(cfg_dir, 'normalization.json'),
            'control_frequency':  20.0,
            'use_odom_steering':  LaunchConfiguration('use_odom_steering'),
            'csv_enabled':        LaunchConfiguration('csv_enabled'),
            'csv_lap_dir':        lap_dir,
        }],
        remappings=[
            ('/odom',          topic_odom),
            ('/ackermann_cmd', topic_ackr),
            ('/path',          topic_path),
            ('/joint_states',  topic_js),
        ],
    )

    return LaunchDescription([
        csv_arg,
        use_odom_steering_arg,
        mpc_node,
    ])
