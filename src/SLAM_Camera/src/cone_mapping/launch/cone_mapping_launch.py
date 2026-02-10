"""
Launch file for cone mapping node with ZED camera integration.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate launch description for cone mapping system."""
    
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error)'
    )
    
    # Cone mapping node
    cone_mapping_node = Node(
        package='cone_mapping',
        executable='cone_mapping_node.py',
        name='cone_mapping_node',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
        arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],
        remappings=[
            # Remap topics if needed
            # ('/perception/landmarks', '/custom/landmarks'),
        ]
    )
    
    # Static transform publisher (example - adjust based on actual calibration)
    # This publishes the fixed transform from base_link to zed_camera
    static_tf_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_camera_broadcaster',
        arguments=[
            '0.3', '0.0', '0.5',  # x, y, z translation
            '0.0', '0.0', '0.0', '1.0',  # qx, qy, qz, qw rotation (identity)
            'base_link',
            'zed_camera'
        ],
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }]
    )
    
    return LaunchDescription([
        use_sim_time_arg,
        log_level_arg,
        cone_mapping_node,
        static_tf_publisher,
    ])
