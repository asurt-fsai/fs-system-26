"""
Launch file for the Voronoi path planning node.

Usage:
    ros2 launch launch/voronoi_planning.launch.py
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Resolve path to the installed parameter file
    config_file = os.path.join(
        get_package_share_directory("planning_voronoi"),
        "config",
        "voronoi_params.yaml",
    )

    voronoi_node = Node(
        package="planning_voronoi",
        executable="voronoi_node",
        name="voronoi_planning_node",
        output="screen",
        parameters=[config_file],
    )

    return LaunchDescription([voronoi_node])
