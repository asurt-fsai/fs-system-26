from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Landmark to Marker Converter Node
        Node(
            package='cone_a_lisa',
            executable='landmark_to_marker',
            name='landmark_visualizer',
            output='screen'
        ),
        
        # Cone Mapper Node
        Node(
            package='cone_a_lisa',
            executable='cone_a_lisa',
            name='cone_mapper',
            output='screen',
            parameters=[
                {'alpha': 0.2},
                {'association_threshold': 1.0}
            ]
        )
    ])