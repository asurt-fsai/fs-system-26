"""
    Represents one ROS module (perception, control, planning, etc.)
    Responsible for managing its lifecycle and state transitions. 
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
from rclpy.node import Node
import time
import psutil
from ModuleState import ModuleState




class Module(Node):

    def __init__(self, pkg: str, launchFile: str):
        self.pkg = pkg
        self.launchFile = launchFile

        self.process: subprocess.Popen | None = None
        self.state = ModuleState.SHUTDOWN

        self.last_restart_time = 0
        self.heartbeat_rate = 0.0
        self.has_heartbeat = False
        self._restart_attempts = 0
        self._max_restart_attempts = 3
    

    # --------------------------------------------------
    # Launch Process
    # --------------------------------------------------
    def launch_Module(self) -> bool:
        """
        Launch the ROS module using ros2 launch.
        """

        if self._state not in [
            ModuleState.Shutdown,
            ModuleState.Error,
            ModuleState.Unresponsive,
        ]:
            print(f"[MODULE] Cannot launch {self.name} from state {self._state.name}")
            return False

        try:
            print(f"[MODULE] Launching {self.package}/{self.launch_file} ...")


            #  Move to Starting state
            self._state = ModuleState.Starting

            # Start ROS process
            self._process = subprocess.Popen(
                ["ros2", "launch", self.package, self.launch_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Reset runtime info
            self._last_heartbeat = None
            self._restart_attempts = 0

            print(f"[MODULE] {self.name} launched successfully (Starting).")

            return True

        except Exception as e:
            print(f"[MODULE] Launch failed for {self.name}: {e}")

            self._state = ModuleState.Error
            self._process = None

            return False


    def shutdown_Module(self) -> None:
        if self._process:
            self._process.terminate()
            self._process.wait()
        self._state = ModuleState.Shutdown


    def restart(self) -> bool:
        """
        Restart the ROS module safely.
        Handles restart attempts, cooldown, and state transitions.
        """

        # Prevent restart in invalid states
        if self._state == ModuleState.Starting:
            print(f"[MODULE] {self.name} is already starting. Restart aborted.")
            return False

        if self._restart_attempts >= self._max_restart_attempts:
            print(f"[MODULE] Max restart attempts reached for {self.name}.")
            self._state = ModuleState.Error
            return False

        # Count this attempt
        self._restart_attempts += 1

        print(
            f"[MODULE] Restarting {self.name} "
            f"(Attempt {self._restart_attempts}/{self._max_restart_attempts})..."
        )

        # Force shutdown of the module
        self.shutdown_Module()

        # Cooldown before relaunch
        time.sleep(2)

        # Try to launch again
        success = self.launch_Module()

        if success:
            print(f"[MODULE] {self.name} restart initiated (Starting state).")
            self._state = ModuleState.Starting
        else:
            print(f"[MODULE] Restart failed for {self.name}.")
            self._state = ModuleState.Error

        return success

    # --------------------------------------------------
    # Heartbeat & Status Callbacks (old code hanshelo b3den)
    # --------------------------------------------------
    def heartbeat_callback(self, msg: NodeStatus) -> None:
        #self.get_logger().info(f" da5alnaaaaa heartbeat_callback Heartbeat received for module: {self.pkg}, Status: {msg.status}, Count before: {self.heartbeat_count}")
        self.state = msg.status
        self.heartbeat_count += 1.0
        # self.get_logger().info(f" Heartbeat count after update : {self.heartbeat_count}")

# msg_callback & heartbeat_callback?? very alike barely know the diff written in notes
    def msg_callback(self, _: NodeStatus) -> None:
        """
        Callback for the topic the module publishes (used if no heartbeat topic is available)
        """
        # self.get_logger().info("Heartbeat received in msg_callback")
        self.state = NodeStatus.RUNNING
        self.heartbeat_count += 1.0

    def update_heartbeat_rate(self) -> None:
        # self.get_logger().info("🔁 update_heartbeat_rate called")
        self.expected_rate = 5
        self.tolerance = 0.7

        now = self.get_clock().now().seconds_nanoseconds()
        current_time = now[0] + now[1] * 1e-9

        if current_time - self.starttime < 7:
            # self.get_logger().info("⏳ Grace period after launch — skipping heartbeat check.")
            return

        time_diff = current_time - self.last_check_time
        if time_diff < 0.2:
            # self.get_logger().warn("⚠️ Skipping heartbeat check — time_diff too small")
            return

        heartbeat_rate = self.heartbeat_count / time_diff

        self.last_check_time = current_time
        self.heartbeat_count = 0
    
        if heartbeat_rate < self.expected_rate * self.tolerance:
            if current_time - self.last_restart_time < 10:
                # self.get_logger().warn("🛑 Skipping restart to avoid restart loop")
                return

            if self.pkg in ["lego_loam_sr", "cone_map"]:
                # self.get_logger().warn(f"❌ Low heartbeat rate ({heartbeat_rate:.2f}) but restart skipped for module: {self.pkg}")
                return

            self.last_restart_time = current_time
            # self.get_logger().warn(
            #     f"❌ Restarting module: rate={heartbeat_rate:.2f}, threshold={self.expected_rate * self.tolerance:.2f}"
            # )
            self.state = ModuleState.Error
            self.restart()
        # else:
        #     self.get_logger().info(f"✅ Heartbeat OK: {heartbeat_rate:.2f} Hz")


