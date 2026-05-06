from launch import LaunchDescription
from launch_ros.actions import Node
import json

def generate_launch_description():

    return LaunchDescription([

        # Central Logger
        Node(
            package='logging_system',
            executable='logger_node',
            name='logger_node',
            output='screen'
        ),

        # System Health Monitor
        Node(
            package='logging_system',
            executable='resource_monitor',
            name='resource_monitor',
            output='screen',
            parameters=[{
                'cpu_process_names': ['conversion_node', 'dl_node', 'planning_centerline_calc_node'],
                'gpu_process_names': ['zed'],
                'overall_cpu_threshold': 80.0,
                'overall_gpu_threshold': 300.0,
                'overall_power__max_threshold': 31.0,
                'overall_power__min_threshold': 9.0,
                'overall_temperature_threshold' : 50.0,
                'process_thresholds': json.dumps({
                    "zed": {"cpu": 90.0, "gpu": 1000.0, "mem": 800.0},
                    "conversion_node": {"cpu": 12, "mem":200},
                    "dl_node": {"cpu": 12.0, "mem": 500},
                    "planning_centerline_calc_node":  {"cpu": 10.0, "mem": 500}
                })
            }]
        ),

        # Rosout Monitor
        Node(
            package='logging_system',
            executable='rosout_monitor',
            name='rosout_monitor',
            output='screen'
        ),

        # Topic Monitor
        Node(
            package='logging_system',
            executable='topic_monitor',
            name='topic_monitor',
            output='screen',
            parameters=[{
                'topics': ['/perception_markers', '/topic2'],
                'timeout': 2.0,
                'expected_freq': json.dumps({
                    "/perception_markers": 10,
                    "/topic2": 10,
                    "/path":10
                }),
                'topic_types': json.dumps({
                    "/perception_markers": "MarkerArray",
                    "/topic2": "Path",
                    "/path":"Path"
                }),
            }]
        ),
    ])
