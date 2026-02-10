"""
Master Launch File for Cone Mapping Testing
Launches cone mapping node with selected test scenario
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    """Generate launch description with test scenario selection."""
    
    # Declare launch arguments
    test_case_arg = DeclareLaunchArgument(
        'test_case',
        default_value='ideal',
        description='Test scenario: ideal, noisy, loop_closure, edge_cases, multilap'
    )
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error)'
    )
    
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz for visualization'
    )
    
    record_bag_arg = DeclareLaunchArgument(
        'record_bag',
        default_value='false',
        description='Record rosbag of test run'
    )
    
    # Get configuration
    test_case = LaunchConfiguration('test_case')
    log_level = LaunchConfiguration('log_level')
    use_rviz = LaunchConfiguration('use_rviz')
    record_bag = LaunchConfiguration('record_bag')
    
    # Cone mapping node
    cone_mapping_node = Node(
        package='cone_mapping',
        executable='cone_mapping_node.py',
        name='cone_mapping_node',
        output='screen',
        parameters=[{
            'use_sim_time': False,
        }],
        arguments=['--ros-args', '--log-level', log_level]
    )
    
    # Static TF publisher (camera to base_link)
    static_tf_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_camera_broadcaster',
        arguments=[
            '0.3', '0.0', '0.5',
            '0.0', '0.0', '0.0', '1.0',
            'base_link',
            'zed_camera'
        ]
    )
    
    # Test Case 1: Ideal Conditions
    test_ideal = Node(
        package='cone_mapping',
        executable='test_case_1_ideal.py',
        name='perception_simulator',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('test_case'), "' == 'ideal'"])
        )
    )
    
    # Test Case 2: Noisy Detections
    test_noisy = Node(
        package='cone_mapping',
        executable='test_case_2_noisy.py',
        name='perception_simulator',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('test_case'), "' == 'noisy'"])
        )
    )
    
    # Test Case 3: Loop Closure
    test_loop_closure = Node(
        package='cone_mapping',
        executable='test_case_3_loop_closure.py',
        name='perception_simulator',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('test_case'), "' == 'loop_closure'"])
        )
    )
    
    # Test Case 4: Edge Cases
    test_edge_cases = Node(
        package='cone_mapping',
        executable='test_case_4_edge_cases.py',
        name='perception_simulator',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('test_case'), "' == 'edge_cases'"])
        )
    )
    
    # Test Case 5: Multi-Lap
    test_multilap = Node(
        package='cone_mapping',
        executable='test_case_5_multilap.py',
        name='perception_simulator',
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('test_case'), "' == 'multilap'"])
        )
    )
    
    # RViz (optional)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(use_rviz)
    )
    
    # Rosbag recording (optional)
    bag_record = ExecuteProcess(
        cmd=['ros2', 'bag', 'record', '-a', '-o', 'test_run'],
        output='screen',
        condition=IfCondition(record_bag)
    )
    
    return LaunchDescription([
        test_case_arg,
        log_level_arg,
        use_rviz_arg,
        record_bag_arg,
        cone_mapping_node,
        static_tf_publisher,
        test_ideal,
        test_noisy,
        test_loop_closure,
        test_edge_cases,
        test_multilap,
        rviz_node,
        bag_record,
    ])



