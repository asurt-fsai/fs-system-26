import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('adaptive_pure_pursuit')
    
    # Path to rviz config
    rviz_cfg = os.path.join(pkg_dir, 'config', 'pp_visualizer.rviz')
    
    viz_node = Node(
        package='adaptive_pure_pursuit',
        executable='adaptive_pp_visualizer',
        name='adaptive_pp_visualizer',
        output='screen',
        parameters=[{
            'car_length':   2.8,
            'car_width':    1.4,
            'wheelbase':    1.575,
        }],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
        additional_env={'GTK_PATH': ''},
    )

    return LaunchDescription([
        viz_node,
        rviz_node,
    ])
