"""
visualizer.launch.py — Standalone RViz visualizer

Launches the mpc_visualizer node + RViz.
Assumes the MPC controller and/or bicycle simulator are already running
and publishing on the expected topics.

Run:
  ros2 launch mpc_controller visualizer.launch.py
"""

import os
import json
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('mpc_controller')
    cfg_dir = os.path.join(pkg_dir, 'config')

    # ── Load nodes.json ──────────────────────────────────────────────────
    nodes_cfg = {'node_names': {'mpc_visualizer': 'mpc_visualizer'},
                 'topics': {'odometry': '/carmaker/Odometry',
                            'reference_path': '/path',
                            'predicted_path': '/mpc/predicted_path',
                            'track_markers': '/mpc/track_markers',
                            'heading_arrow': '/mpc/heading_arrow',
                            'vehicle_footprint': '/mpc/vehicle_footprint',
                            'constraint_markers': '/mpc/constraint_markers',
                            'predicted_path_viz': '/mpc/predicted_path_viz'}}
    try:
        with open(os.path.join(cfg_dir, 'nodes.json')) as f:
            nodes_cfg = json.load(f)
    except Exception:
        pass

    node_name = nodes_cfg['node_names']['mpc_visualizer']

    # ── Load r_inner / r_outer from model.json ───────────────────────────
    r_inner, r_outer = 1.5, 1.5
    try:
        with open(os.path.join(cfg_dir, 'model.json')) as f:
            m = json.load(f)
            r_inner = float(m.get('r_inner', r_inner))
            r_outer = float(m.get('r_outer', r_outer))
    except Exception:
        pass

    rviz_cfg = os.path.join(cfg_dir, 'mpc_test.rviz')

    viz_node = Node(
        package='mpc_controller',
        executable='mpc_visualizer',
        name=node_name,
        output='screen',
        parameters=[{
            'car_length':   2.8,
            'car_width':    1.4,
            'wheelbase':    1.575,
            'track_width':  (r_inner + r_outer) / 2.0,
            'r_inner':      r_inner,
            'r_outer':      r_outer,
            'cone_spacing': 5,
        }],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
        # Unset GTK_PATH to prevent VS Code snap's libpthread from being loaded
        additional_env={'GTK_PATH': ''},
    )

    return LaunchDescription([
        viz_node,
        rviz_node,
    ])
