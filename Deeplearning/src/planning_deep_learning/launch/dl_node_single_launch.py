import launch
import launch_ros.actions


def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='planning_deep_learning',
            executable='dl_node_single_thread',
            output='screen',
        ),
    ])
