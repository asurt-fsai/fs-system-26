from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="supervisor_pkg",
                executable="supervisor_node",
                name="supervisor",
                output="screen",
            ),
            Node(
                package="supervisor_pkg",
                executable="interface",
                name="supervisor_gui",
                output="screen",
            ),
            Node(
                package="supervisor_pkg",
                executable="mission_manager_node",
                name="mission_manager",
                output="screen",
            ),
            Node(
                package="supervisor_pkg",
                executable="module_manager_node",
                name="module_manager",
                output="screen",
            ),
        ]
    )
