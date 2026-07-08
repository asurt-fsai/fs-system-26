from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    id = LaunchDescription()
    perception_node =  Node(
            package='perception_zed_pkg',
            executable='conversion_node'
        )

    loop_closure_node =  Node(
            package='perception_zed_pkg',
            executable='loop_closure_node'
        )

    id.add_action(perception_node)
    id.add_action(loop_closure_node)
    return id
