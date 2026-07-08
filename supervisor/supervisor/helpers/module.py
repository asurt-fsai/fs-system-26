"""
Module class to launch and shutdown modules (launch files)
"""
from enum import Enum
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




class ModuleStateE(Enum):
    """
    Enum class for the module's state:
    """
    Starting     = 0 #mirrors nodestatus.starting
    Ready        = 1 #mirrors nodestatus.ready
    Running      = 2 #mirrors nodestatus.running
    Error        = 3 #mirrors nodestatus.error
    Shutdown     = 4 #mirrors nodestatus.shutdown
    Unresponsive = 5 #supervisor override- doesnt mirror anything in nodestatus
    
class Module(Node):  # Module should inherit from Node properly
    """
    Launches a module (launch file) and checks if it is alive using the optional heartbeat topic
    """

    def __init__(
        self,
        pkg: str,
        launchFile: str,
        heartbeat: Optional[str] = None,
        isHeartbeatNodestatus: bool = True,
        shutdown_callback=None,
        restart_callback=None
        
        
    ) -> None:
        # Ensure ROS 2 is initialized
        if not rclpy.ok():
            rclpy.init()

        # Correctly initialize the Node
        super().__init__("module")
        self.shutdown_callback= shutdown_callback
        self.restart_callback=restart_callback
        self.pkg = pkg
        self.launchFile = launchFile
        self.shutdown_intentional = False #3ashan mission finisher
        #self.state = NodeStatus.SHUTDOWN---- 2 sources of truth= bug 
        self.state = ModuleStateE.Shutdown #state management is done 3ala ModuleStateE bas as of rn 
        self.moduleHandle = None
        self.scheduleRestart = False
        self.hasHeartbeat = heartbeat is not None
        self.rate = 0.0
        self.launch_process =None
        self.last_heartbeat_time = self.get_clock().now().seconds_nanoseconds()[0]
        self.heartbeat_count = 0.0
        self.new_heartbeat_rate=0.0
        #self.ModuleStateE = ModuleStateE.Ready #i added it to fix the isready func
        self.last_restart_time = self.get_clock().now().seconds_nanoseconds()[0]  
        now = self.get_clock().now().seconds_nanoseconds()
        current_time = now[0] + now[1] * 1e-9 
        self.starttime = current_time
        self.last_check_time = current_time

        try:
            # Ensure package and launch file are not None
            assert self.pkg is not None and self.launchFile is not None
        except AssertionError:
            raise ValueError("Supervisor.Module: must have a valid package and launch file.")
        
        # Setup heartbeat subscription if provided
        # All modules use StatusPublisher which publishes NodeStatus messages
        if self.hasHeartbeat:
            try:
                self.get_logger().info(f"📡 Subscribing to heartbeat topic: {heartbeat}")
                self.create_subscription(
                    NodeStatus,
                    heartbeat,
                    self.heartbeat_callback,
                    10
                )
                self.get_logger().info(f"✅ Subscribed to heartbeat topic: {heartbeat}")
                
                self.heartbeat_rate_thread = IntervalTimer(1, self.update_heartbeat_rate)
                self.heartbeat_rate_thread.start()
                self.last_heartbeat_time = self.get_clock().now().seconds_nanoseconds()[0]
                self.heartbeat_count = 0.0
            except Exception as e:
                self.get_logger().error(f"Failed to create subscription: {e}")

    def __repr__(self) -> str:
        return f"{self.pkg} {self.launchFile}"



    def shutdownmodule(self , full_shutdown: bool = True) -> None:
        """
        Shuts down the module.
        """
        self.get_logger().info(f"Shutting down module: {self.pkg}/{self.launchFile}")
        #shutdown intentional
        self.get_logger().info(f"Shutdown intentional value: {self.shutdown_intentional}")
        if full_shutdown:
            if self.hasHeartbeat and self.heartbeat_rate_thread:
                self.heartbeat_rate_thread.stop()

            try:
                self.get_logger().info("Destroying ROS node...")
                self.destroy_node()  # This removes the node from ROS graph
            except Exception as e:
                self.get_logger().error(f"Error destroying node: {e}")   

    def heartbeat_callback(self, msg: NodeStatus):
        ros_to_internal = {
            NodeStatus.STARTING: ModuleStateE.Starting,
            NodeStatus.READY: ModuleStateE.Ready,
            NodeStatus.RUNNING: ModuleStateE.Running,
            NodeStatus.ERROR: ModuleStateE.Error,
            NodeStatus.SHUTDOWN: ModuleStateE.Shutdown,
        }

        self.state = ros_to_internal.get(msg.status, ModuleStateE.Unresponsive)
        self.heartbeat_count += 1.0
    #self.get_logger().info(f" da5alnaaaaa heartbeat_callback Heartbeat received for module: {self.pkg}, Status: {msg.status}, Count before: {self.heartbeat_count}")
        #self.state=ModuleStateE.Running

        #self.state = msg.status
        #self.heartbeat_count += 1.0
        # self.get_logger().info(f" Heartbeat count after update : {self.heartbeat_count}")

# msg_callback & heartbeat_callback?? very alike barely know the diff written in notes
#actually never used , we always use nodestatus
    def msg_callback(self, _: NodeStatus) -> None:
        """
        Callback for the topic the module publishes (used if no heartbeat topic is available)
        """
        # self.get_logger().info("Heartbeat received in msg_callback")
        #self.state=ModuleStateE.Running
        self.heartbeat_count += 1.0

    # def update_heartbeat_rate(self) -> None:
    #     """
    #     Updates the heartbeat rate, called using a looping thread
    #     """

    #     """
    #     ehna mehtageen ne7seb rate el ne check 3aleh 3ashan na3mel restart el howa eh ba2a?
    #     hal howa total heartbeat count /total time 'wala masalan el frequency el heya 100 hz 
    #     """
    #     current_time = self.get_clock().now().seconds_nanoseconds()[0]
    #     self.avg_heartbeat_rate = self.heartbeat_count/(current_time - self.starttime)  # current time - self.starttime (total time)

    #     self.get_logger().info(f"🟢 update_heartbeat_rate function is being called for modlue: {self.launchFile} ")  # Debugging log
        
    #     try:
    #         time_diff = current_time - self.last_heartbeat_time
    #         self.last_heartbeat_time = current_time
            
    #         # self.new_heartbeat_rate = self.heartbeat_count / (time_diff + 0.001)  # Avoid division by zero
    #         self.heartbeat_count = 0

    #         # beta = 0.3  # Smoothing factor
    #         # self.rate = beta * self.rate + (1.0 - beta) * self.new_heartbeat_rate

    #         self.get_logger().info(f"Module status inside update heartbeat: {self.ModuleState}")

    #         # if self.new_heartbeat_rate < 65 and self.ModuleState != ModuleState.Shutdown:
    #         self.get_logger().info(f"Module {self.pkg}/{self.launchFile} heartbeat rate: {self.avg_heartbeat_rate:.2f} bpm")
    #         if self.avg_heartbeat_rate > 90:
    #             self.get_logger().warn("❌ Node marked as UNRESPONSIVE. Restarting...")
    #             self.state=ModuleState.Error
    #             self.get_logger().info(f"will now restart")
    #             self.restart()

    #             # if self.shutdown_callback:
    #             #     self.shutdown_callback()  # 👈 call the function provided by MissionLauncher

            
        # except Exception as e:
        #     self.get_logger().error(f"Error updating heartbeat rate: {e}")
            
    # def update_heartbeat_rate(self) -> None:
    #     self.get_logger().info("🔁 update_heartbeat_rate called")
    #     self.expected_rate = 5 # Expected heartbeat frequency (Hz)
    #     self.tolerance = 0.7      # Acceptable lower bound (e.g., 70Hz)

    #     now = self.get_clock().now().seconds_nanoseconds()
    #     current_time = now[0] + now[1] * 1e-9  # Get time in seconds (float)


    # #  Skip everything during the grace period
    #     if current_time - self.starttime < 7:
    #         self.get_logger().info("⏳ Grace period after launch — skipping heartbeat check.")
    #         return

    #     time_diff = current_time - self.last_check_time
    #     if time_diff == 0:
    #         self.get_logger().warn("⛔ Skipping rate calculation to avoid division by zero.")
    #         return

    #     heartbeat_rate = self.heartbeat_count / time_diff

    #     self.get_logger().info(f"❤️ Heartbeat rate: {heartbeat_rate:.2f} Hz over {time_diff:.2f} seconds")

    #     self.last_check_time = current_time
    #     self.heartbeat_count = 0

    #     # if heartbeat_rate > 200000: just testing mafrood mayedkholsh khales 
    #     if heartbeat_rate < self.expected_rate * self.tolerance:
    #         if current_time - self.last_restart_time < 10:
    #             self.get_logger().warn("🛑 Skipping restart to avoid restart loop")
    #             return
    #         self.last_restart_time = current_time
    #         self.get_logger().warn("❌ Node marked as UNRESPONSIVE. Restarting...")
    #         self.state = ModuleState.Error
    #         self.restart()

    #     else:
    #         self.get_logger().info(f"✅ NAH wont restart, heartbeat rate is {heartbeat_rate:.2f}")

    def update_heartbeat_rate(self) -> None:

        if self.shutdown_intentional:
            self.get_logger().info("Module shutdown is intentional, skipping heartbeat check.")
            return

        # self.get_logger().info("🔁 update_heartbeat_rate called")
        self.expected_rate = 5
        self.tolerance = 0.7
        
        # self.expected_rate = 0  # garabt al3ab mfesh natega - mghyrtsh haga tanya
        # self.tolerance = 0
        
        now = self.get_clock().now().seconds_nanoseconds()
        current_time = now[0] + now[1] * 1e-9

        if current_time - self.starttime < 7: #was 7 used 20 for deep learning because its very slow will adjust when i actually measure how long dl takes
            # self.get_logger().info("⏳ Grace period after launch — skipping heartbeat check.")
            return

        time_diff = current_time - self.last_check_time
        if time_diff < 0.2:
            # self.get_logger().warn("⚠️ Skipping heartbeat check — time_diff too small")
            return

        heartbeat_rate = self.heartbeat_count / time_diff

        # self.get_logger().info(f"❤️ Heartbeat rate: {heartbeat_rate:.2f} Hz over {time_diff:.2f} seconds")
        # self.get_logger().info(f"[DEBUG] heartbeat_count = {self.heartbeat_count}, time_diff = {time_diff:.2f}")
        # self.get_logger().info(f"[DEBUG] threshold = {self.expected_rate * self.tolerance:.2f}")
        #print module and its heartbeat rate
        # self.get_logger().info(f"Module {self.pkg}/{self.launchFile} heartbeat rate: {heartbeat_rate:.2f} Hz over {time_diff:.2f} seconds")
        


        self.last_check_time = current_time
        self.heartbeat_count = 0
    
        if heartbeat_rate < self.expected_rate * self.tolerance:
            if current_time - self.last_restart_time < 10:
                # self.get_logger().warn("🛑 Skipping restart to avoid restart loop")
                return

            #if self.pkg in ["lego_loam_sr", "cone_map"]:
                # self.get_logger().warn(f"❌ Low heartbeat rate ({heartbeat_rate:.2f}) but restart skipped for module: {self.pkg}")
            #    return

            self.last_restart_time = current_time
            # self.get_logger().warn(
            #     f"❌ Restarting module: rate={heartbeat_rate:.2f}, threshold={self.expected_rate * self.tolerance:.2f}"
            # )
            self.state = ModuleStateE.Error
            self.restart()
        # else:
        #     self.get_logger().info(f"✅ Heartbeat OK: {heartbeat_rate:.2f} Hz")


    def launch(self) -> None:
        """
        Launch the module using ROS 2 launch files
        """
        self.get_logger().info(f"Launching module: {self.pkg}/{self.launchFile}")
        
    

        try:
            pkg_share_dir = os.path.join(os.getenv('ROS_PACKAGE_PATH', ''), self.pkg, 'launch')
            launch_file_path = os.path.join(pkg_share_dir, self.launchFile)
        
        # Start the ROS 2 launch process in a separate process
            self.launch_process = subprocess.Popen(
                ["ros2", "launch", self.pkg, self.launchFile],
                #stdout=subprocess.PIPE,
                #stderr=subprocess.PIPE
                stdout= None,
                stderr= None
            )

            self.get_logger().info(f"Launched {self.pkg}/{self.launchFile} (PID: {self.launch_process.pid})")
            #self.state = ModuleStateE.Running --badry awi lazem akhod heartbeat el awal
            self.state = ModuleStateE.Starting
            """
            if self.hasHeartbeat:
                # Start a heartbeat thread
                self.heartbeat_thread = self.start_heartbeat()
            """
        except Exception as e:
            self.get_logger().error(f"Failed to launch module: {e}")
            self.state = ModuleStateE.Error


    def restart(self) -> None:
        """
        Restarts the module by shutting it down and launching it again.
        """
        if self.shutdown_intentional:
            self.get_logger().info("Module shutdown is intentional, skipping restart.")
            return
        try:
            self.get_logger().info(f"Restarting module: {self.pkg}/{self.launchFile}")
            # self.get_logger().info("BEFORE SLEEP: GOOD NIGHT")
            self.shutdownmodule(full_shutdown=False)
            self.shutdownlaunchfile()
            # time.sleep(10)
            # self.get_logger().info("AFRER SLEEP: GOOD MORNING")
            self.launch()
            self.get_logger().info(f"Module {self.pkg}/{self.launchFile} restarted successfully.")
            now = self.get_clock().now().seconds_nanoseconds()
            current_time = now[0] + now[1] * 1e-9
            self.last_check_time = current_time
            self.starttime = current_time

            #self.last_check_time=0
            self.get_logger().info(f"Counter reset.")
        except Exception as e:
            self.get_logger().error(f"Error during restart: {e}")
            self.state = ModuleStateE.Error        


    def run_launch_service(self):
        """
        Runs the LaunchService in a separate thread but ensures it's handled properly.
        """
        try:
            self.get_logger().info("🔄 Running ROS 2 spin loop for subscriptions...")
            rclpy.spin(self)
        except Exception as e:
            self.get_logger().error(f"Error while running launch service: {e}")


    def __del__(self) -> None:
        """
        Destructor to ensure proper shutdown
        """
        try:
            self.shutdown()
        except Exception as e:
            self.get_logger().error(f"Error in destructor: {e}")


    def shutdownlaunchfile(self):
        """
        Shuts down the launch process safely, with debug logs
        """
        self.get_logger().info("Starting shutdown sequence...")

        if self.launch_process:
            try:
                # Debug: What type is launch_process?
                self.get_logger().info(f"Type of launch_process: {type(self.launch_process)}")

                # Debug: Check if it's a subprocess.Popen
                if not isinstance(self.launch_process, subprocess.Popen):
                    self.get_logger().error("launch_process is NOT a subprocess.Popen instance")
                    self.state = ModuleStateE.Error
                    return

                # Debug: Check if the process is already terminated
                poll_result = self.launch_process.poll()
                self.get_logger().info(f"launch_process.poll() returned: {poll_result}")
                if poll_result is not None:
                    self.get_logger().warn("Launch process already exited before shutdown attempt.")

                # Try to kill using psutil for robustness
                parent = psutil.Process(self.launch_process.pid)
                children = parent.children(recursive=True)

                self.get_logger().info(f"Terminating {len(children)} child processes...")
                for child in children:
                    self.get_logger().info(f"Terminating child PID: {child.pid}")
                    child.terminate()

                self.get_logger().info(f"Terminating parent PID: {parent.pid}")
                parent.terminate()

                gone, alive = psutil.wait_procs([parent] + children, timeout=5)

                self.get_logger().info(f"Processes terminated: {[p.pid for p in gone]}")
                if alive:
                    self.get_logger().warn(f"Some processes still alive: {[p.pid for p in alive]}")

                self.get_logger().info("Launch process shut down successfully")
                self.state = ModuleStateE.Shutdown  


            except Exception as e:
                self.get_logger().error(f"Exception during shutdown: {repr(e)}")
                self.state = ModuleStateE.Error
        else:
            self.get_logger().warn("No launch_process found to shut down.")
            self.state = ModuleStateE.Error



    def stop_monitoring_for_shutdown(self) -> None:
            """
            Stop heartbeat monitoring before intentional mission shutdown.
            This prevents the module from restarting while we are killing it.
            """

            self.shutdown_intentional = True

            if self.hasHeartbeat and hasattr(self, "heartbeat_rate_thread"):
                try:
                    self.heartbeat_rate_thread.stop()
                    self.get_logger().info(
                        f"Heartbeat monitoring stopped for {self.pkg}/{self.launchFile}"
                    )
                except Exception as e:
                    self.get_logger().error(
                        f"Failed to stop heartbeat monitoring for {self.pkg}: {e}"
                    )