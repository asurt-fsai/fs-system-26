import os
import launch
import launch_ros.actions
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Path to the YAML file containing the parameters
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    param_dir = os.path.join(get_package_share_directory('supervisor'), 'config', 'supervisor_params.yaml')
    param_dir_finisher = os.path.join(get_package_share_directory('supervisor'), 'config', 'mission_finisher_params.yaml')
    supervisor_node = launch_ros.actions.Node(
        package='supervisor',
        executable='supervisor_node',
        parameters=[param_dir],
        output='screen'
    )

    status_node = launch_ros.actions.Node(
        package='supervisor',
        executable='status',
        output='screen'
    )

    gui_node = launch_ros.actions.Node(
        package='supervisor',
        executable='testgui',
        output='screen'
    )



    mission_finisher_node = launch_ros.actions.Node(
        package='supervisor',
        executable='mission_finisher',
        parameters=[param_dir_finisher],
        output='screen'
    )
    
   # odom_tracker_node = launch_ros.actions.Node(
    #    package='supervisor',
     #   executable='odom_tracker',
      #  name='odom_tracker',
       # output='screen'
   # )
    
    loop_closure_node = launch_ros.actions.Node(
        package='perception_zed_pkg',
        executable='loop_closure_node',
        name='loop_closure_node',
        output='screen'
    )
    
    
    return launch.LaunchDescription([
        DeclareLaunchArgument(
            'param_dir',
            default_value=param_dir,
            description='Full path to the parameter file to load'),
        supervisor_node,
        mission_finisher_node,
        status_node,
        gui_node,
        #odom_tracker_node
        loop_closure_node

    ])

if __name__ == '__main__':
    generate_launch_description()
