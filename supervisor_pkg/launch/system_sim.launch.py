"""
Simulation launch — same as system.launch.py but adds the VCU simulator.
Use this instead of system.launch.py when testing without the real vehicle.

ami_state parameter:
  18 = Static A
  19 = Static B
  15 = AutoDemo
  13 = Autocross
  14 = Trackdrive

After launch, step the VCU state machine manually:
  ros2 service call /vcu_next_state std_srvs/srv/Trigger {}   # AS_OFF -> AS_READY -> AS_DRIVING ...
  ros2 service call /vcu_prev_state std_srvs/srv/Trigger {}   # step back
  ros2 service call /ros_can/ebs    std_srvs/srv/Trigger {}   # force EBS
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    ami_arg = DeclareLaunchArgument(
        "ami_state",
        default_value="18",
        description="AMI mission state (18=StaticA, 19=StaticB, 15=AutoDemo)",
    )

    return LaunchDescription([
        ami_arg,

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
            executable="vcu_simulator",
            name="vcu_simulator",
            output="screen",
            parameters=[{"ami_state": LaunchConfiguration("ami_state")}],
        ),
    ])
