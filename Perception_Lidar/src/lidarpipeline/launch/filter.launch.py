import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess


def generate_launch_description():
    package_name = 'lidarpipeline'
    bag_path = '/home/malak/Desktop/RT/ARL/baggg/MainPointCloudBag'

    config_path = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'params.yaml'
    )

    return LaunchDescription([
        # 1. Play the Rosbag
       ExecuteProcess(
           cmd=['ros2', 'bag', 'play', bag_path],
           output='screen'
         ),

        # 2. Lidar Processor Node
        Node(
            package=package_name,
            executable='lidar_processor_node',
            name='lidar_processor_node',
            output='screen',
            remappings=[
                ('/points', '/velodyne_points')
            ],
            parameters=[
                config_path,
                {'use_sim_time': True}
            ]
        ),

        # 3. RViz2
        #Node(
        #    package='rviz2',
        #    executable='rviz2',
        #    name='rviz2',
        #    output='screen'
       # )
    ])
