"""
Integrated Launch File for Perception + SLAM
Launches all components needed for real camera integration:
1. perception_zed conversion node (subscribes to ZED raw detections)
2. message_adapter (converts asurt_msgs ↔ cone_mapping messages)
3. cone_mapping_node (performs SLAM and mapping)
4. static_transform_publisher (camera calibration)
5. Optional: RViz for visualization
6. Optional: rosbag recording

Usage:
    ros2 launch cone_mapping integrated_launch.py
    ros2 launch cone_mapping integrated_launch.py use_rviz:=true
    ros2 launch cone_mapping integrated_launch.py use_rviz:=true record_bag:=true
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os


def generate_launch_description():
    """Generate launch description with all integrated nodes."""
    
    # Declare launch arguments
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz for visualization'
    )
    
    record_bag_arg = DeclareLaunchArgument(
        'record_bag',
        default_value='false',
        description='Record rosbag of integrated run'
    )
    
    log_level_arg = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error)'
    )
    
    # Get configuration
    use_rviz = LaunchConfiguration('use_rviz')
    record_bag = LaunchConfiguration('record_bag')
    log_level = LaunchConfiguration('log_level')
    
    # =========================================================================
    # 1. Perception ZED Node
    # Subscribes to: /zed/zed_node/obj_det/objects (ZED camera detections)
    # Publishes to: /perception/landmarks (asurt_msgs::LandmarkArray)
    # =========================================================================
    perception_node = Node(
        package='perception_zed_pkg',
        executable='conversion_node',
        name='zed_to_landmark',
        output='screen',
        arguments=['--ros-args', '--log-level', log_level]
    )
    
    # =========================================================================
    # Pose Republisher
    # Republishes incoming ZED pose so downstream nodes can subscribe here
    # =========================================================================
    launch_dir = os.path.dirname(os.path.abspath(__file__))
    install_root = os.path.normpath(os.path.join(launch_dir, '..', '..', '..'))
    installed_pose = os.path.join(install_root, 'lib', 'cone_mapping', 'pose_republisher')
    source_pose = os.path.normpath(os.path.join(launch_dir, '..', '..', 'cone_mapping', 'pose_republisher.py'))
    # If source path points into the installed tree (when launch executed from install),
    # search upward for workspace root that contains the source package.
    if not os.path.exists(source_pose):
        for up in range(1, 7):
            candidate_root = os.path.normpath(os.path.join(launch_dir, *(['..'] * up)))
            candidate_pose = os.path.join(candidate_root, 'src', 'SLAM_Camera', 'src', 'cone_mapping', 'cone_mapping', 'pose_republisher.py')
            if os.path.exists(candidate_pose):
                source_pose = candidate_pose
                break
    if os.path.exists(installed_pose):
        pose_republisher_node = Node(
            package='cone_mapping',
            executable='pose_republisher',
            name='pose_republisher',
            output='screen',
            arguments=['--ros-args', '--log-level', log_level]
        )
    else:
        pose_republisher_node = ExecuteProcess(
            cmd=['python3', source_pose, '--ros-args', '--log-level', log_level],
            output='screen'
        )
    
    # =========================================================================
    # 2. Cone Mapping Node (SLAM)
    # Subscribes to: 
    #   - /perception/landmarks (cone_mapping messages from conversion_node)
    #   - /zed/zed_node/pose (vehicle pose)
    # Publishes to: /map/global_cones (confirmed landmarks)
    # =========================================================================
    # Detect paths for source code fallback (when running from source tree)
    launch_dir = os.path.dirname(os.path.abspath(__file__))
    install_root = os.path.normpath(os.path.join(launch_dir, '..', '..', '..'))
    installed_node = os.path.join(install_root, 'lib', 'cone_mapping', 'cone_mapping_node')

    source_module_path = os.path.normpath(os.path.join(launch_dir, '..', '..', 'cone_mapping'))
    source_node = os.path.join(source_module_path, 'cone_mapping_node.py')

    # If running the launch file from the installed location, the above
    # source paths will point inside `install/...` which is not the workspace
    # source tree. As a fallback, search upward for a workspace root that
    # contains the source package at `src/SLAM_Camera/src/cone_mapping/cone_mapping`.
    if not os.path.exists(source_node):
        for up in range(1, 7):
            candidate_root = os.path.normpath(os.path.join(launch_dir, *(['..'] * up)))
            candidate_node = os.path.join(candidate_root, 'src', 'SLAM_Camera', 'src', 'cone_mapping', 'cone_mapping', 'cone_mapping_node.py')
            if os.path.exists(candidate_node):
                source_node = candidate_node
                break

    if os.path.exists(installed_node):
        cone_mapping_node = Node(
            package='cone_mapping',
            executable='cone_mapping_node',
            name='cone_mapping_node',
            output='screen',
            arguments=['--ros-args', '--log-level', log_level]
        )
    else:
        cone_mapping_node = ExecuteProcess(
            cmd=['python3', source_node, '--ros-args', '--log-level', log_level],
            output='screen'
        )
    
    # =========================================================================
    # 3. Static Transform Publisher
    # Publishes TF: base_link → zed_camera (camera calibration)
    # Calibration parameters: 
    #   position: [0.3m forward, 0.0m lateral, 0.5m up]
    #   rotation: identity (camera points forward)
    # =========================================================================
    static_tf_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_camera_broadcaster',
        arguments=[
            '0.3', '0.0', '0.5',      # x, y, z translation (meters)
            '0.0', '0.0', '0.0', '1.0',  # quaternion (identity)
            'base_link',
            'zed_camera'
        ]
    )
    
    # =========================================================================
    # 5. RViz Visualization (Optional)
    # =========================================================================
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(use_rviz)
    )
    
    # =========================================================================
    # 6. ROS Bag Recording (Optional)
    # Records all topics for post-analysis
    # =========================================================================
    bag_record = ExecuteProcess(
        cmd=['ros2', 'bag', 'record', '-a', '-o', 'integrated_run'],
        output='screen',
        condition=IfCondition(record_bag)
    )
    
    # Return launch description
    return LaunchDescription([
        use_rviz_arg,
        record_bag_arg,
        log_level_arg,
        perception_node,
        pose_republisher_node,
        cone_mapping_node,
        static_tf_publisher,
        rviz_node,
        bag_record,
    ])
