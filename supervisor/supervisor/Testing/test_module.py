import os
import subprocess
from ament_index_python.packages import get_package_share_directory

def run_terminal_command(command):
    try:
        # Open a terminal and execute the command
         subprocess.run(['gnome-terminal', '--', 'bash', '-c', command])
    except FileNotFoundError:
        print("Error: gnome-terminal is not installed or not found on your system.")

def launch_ros2_files(pkg, launch_files):
    for launch_file in launch_files:
        # Construct the command to source ROS 2 environment and launch the file
        command = f'source /opt/ros/humble/setup.bash; ros2 launch {pkg} {launch_file}'
        run_terminal_command(command)

if __name__ == "__main__":
    # Package name and list of launch files
    pkg_name = 'planning_acceleration'
    launch_file_names = ['acceleration_launch.py']

    # Launch each file in a new terminal
    launch_ros2_files(pkg_name, launch_file_names)
