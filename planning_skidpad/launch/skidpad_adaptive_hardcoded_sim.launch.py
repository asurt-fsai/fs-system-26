import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description() -> LaunchDescription:
    # Configurations
    skidpad_config = os.path.join(
        get_package_share_directory("planning_skidpad"), "config", "params.yaml"
    )

    # Hardcoded Path Planner Only
    skidpad_hardcoded_planner_node = Node(
        package="planning_skidpad",
        executable="skidpad_hardcoded_planner",
        name="skidpad_hardcoded_planner",
        output="screen",
        parameters=[skidpad_config],
    )

    launchDescription = LaunchDescription()
    launchDescription.add_action(skidpad_hardcoded_planner_node)
    
    return launchDescription
