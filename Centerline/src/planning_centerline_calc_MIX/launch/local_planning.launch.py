import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # Grab your existing parameter file
    config = os.path.join(get_package_share_directory("planning_centerline_calc"), "config", "planning_parameters.yaml")

    # Launch ONLY the local node
    local_planning_node = Node(
        package="planning_centerline_calc",
        executable="local_planning_node", # This matches the name we just put in setup.py
        name="local_planning_node",
        output="screen",
        parameters=[
            config, # Load all the standard math/sorting parameters
            #{
                # Override the topics to use CarMaker's local ground-truth
            #    'planning.topics.conesTopic': '/carmaker/ObjectList',
            #    'planning.topics.frame_id': 'Fr1A'
            #}
        ],
    )

    ld = LaunchDescription()
    ld.add_action(local_planning_node)

    return ld
