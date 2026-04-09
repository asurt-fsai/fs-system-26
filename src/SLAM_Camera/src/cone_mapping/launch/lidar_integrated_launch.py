"""
Integrated Launch File for LiDAR SLAM Pipeline
Launches:
1. The Lidar Perception Pipeline (filtering & clustering from bag)
2. The Cone Mapping Node (SLAM anchoring & mapping)
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    log_level = LaunchConfiguration('log_level', default='info')

    # 1. Include the lidarpipeline launch
    # This launch file handles: playing the rosbag, running lidar_processor_node, and rviz.
    lidar_launch_path = os.path.join(
        get_package_share_directory('lidarpipeline'),
        'launch',
        'filter.launch.py'
    )
    
    lidarpipeline_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_path)
    )

    # 2. Add the Cone Mapping Node
    # It listens to /perception/landmarks emitted by lidarpipeline 
    # and /aft_mapped_to_init (from LeGO-LOAM if running externally).
    cone_mapping_node = Node(
        package='cone_mapping',
        executable='cone_mapping_node.py',
        name='cone_mapping_node',
        output='screen',
        arguments=['--ros-args', '--log-level', log_level],
        # If running from a bag file, we usually need to trust the bag's time
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        lidarpipeline_launch,
        cone_mapping_node
    ])
