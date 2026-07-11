#!/usr/bin/env python3
"""
Launch file for ROS CAN simulation setup
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    can_interface_arg = DeclareLaunchArgument(
        'can_interface',
        default_value='vcan0',
        description='CAN interface to use'
    )
    
    can_debug_arg = DeclareLaunchArgument(
        'can_debug',
        default_value='1',
        description='Enable CAN debug mode'
    )
    
    simulate_can_arg = DeclareLaunchArgument(
        'simulate_can',
        default_value='1',
        description='Enable CAN simulation mode'
    )
    
    # Setup virtual CAN interface
    setup_vcan = ExecuteProcess(
        cmd=['sudo', 'modprobe', 'vcan'],
        name='setup_vcan_module'
    )
    
    create_vcan = ExecuteProcess(
        cmd=['sudo', 'ip', 'link', 'add', 'dev', 'vcan0', 'type', 'vcan'],
        name='create_vcan_interface'
    )
    
    enable_vcan = ExecuteProcess(
        cmd=['sudo', 'ip', 'link', 'set', 'up', 'vcan0'],
        name='enable_vcan_interface'
    )
    
    # ROS CAN node (your original node)
    ros_can_node = Node(
        package='ros_can',  # Replace with your actual package name
        executable='ros_can_node',  # Replace with your actual executable name
        name='ros_can',
        parameters=[{
            'can_interface': LaunchConfiguration('can_interface'),
            'can_debug': LaunchConfiguration('can_debug'),
            'simulate_can': LaunchConfiguration('simulate_can'),
            'loop_rate': 50,
            'debug_logging': True
        }],
        output='screen'
    )
    
    # VCU Simulator node
    vcu_simulator_node = Node(
        package='ros_can',  # Replace with your actual package name
        executable='vcu_simulator.py',
        name='vcu_simulator',
        output='screen'
    )
    
    return LaunchDescription([
        can_interface_arg,
        can_debug_arg,
        simulate_can_arg,
        setup_vcan,
        create_vcan,
        enable_vcan,
        ros_can_node,
        vcu_simulator_node,
    ])