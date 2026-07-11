"""
Launch file for local cone mapping node.
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def resolve_source_node_path(launch_dir: str) -> str:
    """Resolve the local cone mapping script from either source or install paths."""
    candidates = [
        os.path.join(launch_dir, '..', 'cone_mapping', 'cone_mapping_node_locally.py'),
    ]

    for up in range(1, 8):
        base = os.path.normpath(os.path.join(launch_dir, *(['..'] * up)))
        candidates.append(
            os.path.join(base, 'src', 'SLAM_Camera', 'src', 'cone_mapping', 'cone_mapping', 'cone_mapping_node_locally.py')
        )
        candidates.append(os.path.join(base, 'cone_mapping', 'cone_mapping_node_locally.py'))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0]


def generate_launch_description():
    """Generate launch description for local cone mapping."""
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )

    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error)'
    )

    log_level = LaunchConfiguration('log_level')

    launch_dir = os.path.dirname(os.path.abspath(__file__))
    source_node = os.path.normpath(resolve_source_node_path(launch_dir))

    package_share_dir = get_package_share_directory('cone_mapping')
    install_root = os.path.normpath(os.path.join(package_share_dir, '..', '..'))
    installed_node_path = os.path.join(
        install_root,
        'lib',
        'cone_mapping',
        'cone_mapping_node_locally'
    )

    if os.path.exists(installed_node_path):
        cone_mapping_node = Node(
            package='cone_mapping',
            executable='cone_mapping_node_locally',
            name='cone_mapping_node_locally',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
            arguments=['--ros-args', '--log-level', log_level],
        )
    else:
        cone_mapping_node = ExecuteProcess(
            cmd=['python3', source_node, '--ros-args', '--log-level', log_level],
            output='screen',
        )

    return LaunchDescription([
        use_sim_time_arg,
        log_level_arg,
        cone_mapping_node,
    ])
