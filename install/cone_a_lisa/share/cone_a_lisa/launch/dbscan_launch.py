import launch
import launch_ros.actions

def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='dbscan_processing',
            executable='bag_publisher',
            name='bag_publisher',
            output='screen'
        ),
        launch_ros.actions.Node(
            package='dbscan_processing',
            executable='dbscan_slam_node',
            name='dbscan_slam_node',
            output='screen'
        ),
        launch_ros.actions.Node(
            package='dbscan_processing',
            executable='hungarian',
            name='hungarian',
            output='screen'
        ),
        launch_ros.actions.Node(
            package='dbscan_processing',
            executable='EKF',
            name='EKF',
            output='screen'
        ),
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        )
    ])
