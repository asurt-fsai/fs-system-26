import os
import subprocess
import signal
import time
import psutil

# Global list to store terminal process IDs
terminal_processes = []

def run_terminal_command(command):
    try:
        # Open a terminal and execute the command
        process = subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command])
        # Store the terminal's process ID
        return process.pid  # Return the process ID
    except FileNotFoundError:
        print("Error: gnome-terminal is not installed or not found on your system.")
        return None

def get_child_pids(pid):
    try:
        parent = psutil.Process(pid)
        return [child.pid for child in parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        return []

def launch_ros2_files(pkgs, launch_files):
    for launch_file, pkg in zip(launch_files, pkgs):
        # Construct the command to source ROS 2 environment and launch the file
        command = f'source /opt/ros/humble/setup.bash && ros2 launch {pkg} {launch_file}'
        pid = run_terminal_command(command)
        if pid is not None:
            terminal_processes.append(pid)  # Store the process ID
            print(f"Launched terminal for {pkg} - {launch_file} with PID {pid}")
        else:
            print(f"Failed to launch terminal for {pkg} - {launch_file}")

def close_terminal(pid):
    if pid in terminal_processes:
        try:
            # Use pkill to terminate the terminal and its child processes
            os.system(f"pkill -P {pid}")
            os.kill(pid, signal.SIGKILL)  # Send SIGKILL signal to terminate the process
            terminal_processes.remove(pid)  # Remove from list after termination
            print(f"Closed terminal with PID {pid}")
        except ProcessLookupError:
            print(f"Failed to close terminal with PID {pid}: Process not found")
    else:
        print(f"Terminal with PID {pid} not found in active processes.")

if __name__ == "__main__":
    # Package names and list of launch files
    pkg_names = ['planning_acceleration', 'simple_pure_pursuit']
    launch_file_names = ['acceleration_launch.py', 'simplePurePursuit.launch.py']

    # Launch each file in a new terminal
    launch_ros2_files(pkg_names, launch_file_names)
    print(terminal_processes)

    # Example: Close terminal with a specific PID (replace with actual PID)
    if terminal_processes:
        close_terminal(terminal_processes[0])
          # Allow time for the terminal to close
        
        # Optionally, relaunch a specific package and launch file
        pkg_namess = ['planning_acceleration']
        launch_file_namesss = ['acceleration_launch.py']
        launch_ros2_files(pkg_namess, launch_file_namesss)
       
        print(terminal_processes)
        # Optionally, close another terminal
        if len(terminal_processes) > 0:
            close_terminal(terminal_processes[1])
