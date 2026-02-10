from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    id = LaunchDescription()
    perception_node =  Node(
            package='perception_zed_pkg',
            executable='conversion_node'
        )
    id.add_action(perception_node)
    return id
