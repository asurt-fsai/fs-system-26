import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    # 1. Setup Paths
    package_name = 'lidarpipeline'
    bag_path = '/home/eyad/Desktop/Testing_SLAM_(LiDAR)/src/Lidar_Perception/lidarpipeline/data'
    
    #
    
    # Path to your new YAML parameter file
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

        # 2. Your Lidar Processor Node
        Node(
            package=package_name,
            executable='lidar_processor_node',
            name='lidar_processor_node',
            output='screen',
            remappings=[
                ('/points', '/velodyne_points')
            ],
            # Pass the path to the YAML file here
            # Note: Individual dict parameters (like use_sim_time) 
            # can still be added to the list
            parameters=[
                config_path, 
                {'use_sim_time': True}
            ]
        ),

        # 3. RViz2 for Visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        )
    ])