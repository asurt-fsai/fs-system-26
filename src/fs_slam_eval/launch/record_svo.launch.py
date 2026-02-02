#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # --- 1. Define Arguments ---
    svo_arg = DeclareLaunchArgument(
        'svo_file',
        description='Full path to the .svo file to play'
    )
    
    output_name_arg = DeclareLaunchArgument(
        'output_name',
        description='Name of the output MCAP folder'
    )

    # --- 2. Locate Config Files ---
    # We need to find where the 'zed_race_mode.yaml' is installed
    config_common = os.path.join(
        get_package_share_directory('fs_slam_eval'),
        'config', 'zed_race_mode.yaml'
    )
    
    # --- 3. The ZED Wrapper Node ---
    # This plays the video and calculates the position
    zed_wrapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('zed_wrapper'), 'launch', 'zed_camera.launch.py')
        ),
        launch_arguments={
            'camera_model': 'zed2i',
            'svo_path': LaunchConfiguration('svo_file'),
            'ros_params_override_path': config_common, # Load our custom "Race Mode" settings
            'svo_loop': 'false',          # Stop when video ends
            'publish_urdf': 'true'
        }.items()
    )

    # --- 4. The Recorder ---
    # Records the trajectory so Evo can analyze it later
    recorder = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', LaunchConfiguration('output_name'),
            '/zed/zed_node/pose',
            '/zed/zed_node/odom',
            '/zed/zed_node/path_odom',
            '/zed/zed_node/path_map'
        ],
        output='screen'
    )

    return LaunchDescription([
        svo_arg,
        output_name_arg,
        zed_wrapper,
        recorder
    ])