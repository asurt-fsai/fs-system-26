"""
Module class for the supervisor node to manage the nodes 
"""


from typing import Optional
import subprocess
import rclpy
from asurt_msgs.msg import NodeStatus
from .intervalTimer import IntervalTimer
import os
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchService
from launch.actions import IncludeLaunchDescription
#from launch_ros.actions import Node
from rclpy.node import Node
import time
import psutil
