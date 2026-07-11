import os
import json
from typing import List, Dict, Optional
from .intervalTimer import IntervalTimer
from supervisor.helpers.module import ModuleStateE
import rclpy
from rclpy.node import Node
import time
from eufs_msgs.msg import CanState
from asurt_msgs.msg import NodeStatus
from ament_index_python.packages import get_package_share_directory
from .module import Module
from .visualizer import Visualizer
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Bool
from functools import partial
from std_msgs.msg import Float32, String, Int16
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy
from ..nodes.subb import subb
from asurt_msgs.msg import NodeStatus

AMIToConfig = {
    CanState.AMI_DDT_INSPECTION_A: "staticA",
    CanState.AMI_DDT_INSPECTION_B: "staticB",
    CanState.AMI_AUTONOMOUS_DEMO: "autonomousDemo",
    CanState.AMI_AUTOCROSS: "autocross",
    CanState.AMI_SKIDPAD: "skidpad",
    CanState.AMI_ACCELERATION: "acceleration",
    CanState.AMI_TRACK_DRIVE: "trackDrive",
}

"""
def map_state_to_int(state_str: str) -> int:
    state_map = {
        "starting": 0,
        "ready": 1,
        "running": 2,
        "error": 3,
        "shutdown": 4,
        "unresponsive": 5
    }
    return state_map.get(state_str.lower(), -1)  # Return -1 if the state string is not found
"""

class MissionLauncher(Node):
    # Class variables for singleton pattern
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MissionLauncher, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, add_node_callback) -> None:
        # Only initialize once using the singleton pattern
        if not MissionLauncher._initialized:
            super().__init__('mission_launcher_node')
            self.missionType = "Not Selected"
            self.isLaunched = False
            self.modules: List[Module] = []
            self.terminal_processes = []  # Change to a list to store process IDs
            self.lastHeartbeatTime = time.time()
            self.heartbeatCount = 0
            self.drivinfgFlagPub = self.create_publisher(Bool, '/supervisor/driving_flag', 10)
            self.rate = 0
            self.state = NodeStatus.SHUTDOWN #mesh 3agbaniiii han8ayarek
            MissionLauncher._initialized = True
            self.add_node_callback = add_node_callback

            """ self.state_simple_pure_pursuit = NodeStatus.SHUTDOWN
            self.heartbeatCountsimple_pure_pursuit = 0

            self.state_accerleration = NodeStatus.SHUTDOWN
            self.heartbeatCountaccerleration = 0
            """
            self.get_logger().info("MissionLauncher singleton instance initialized")

    def openConfig(self, fileName: str) -> Dict[str, List[Dict[str, str]]]:
        '''
        Opens a JSON file and returns the content as a dictionary

        Args:
            fileName (str): The name of the JSON file to open
        '''
        with open(
            os.path.join(get_package_share_directory('supervisor'), 'json', fileName),
            encoding="utf-8",
        ) as configFile:
            config = json.load(configFile)
        return config

    def launch(self, mission: int) -> None:
        """
        Launches a mission based on the mission type received
        """
        if self.isLaunched:
            self.get_logger().info("Trying to launch a mission while another mission is running, ignoring")
            return

        if mission == -1:
            config = self.openConfig("testConfig.json")
            self.missionType = "test mission"
        else:
            try:
                config = self.openConfig(AMIToConfig[mission] + ".json")
                self.missionType = AMIToConfig[mission]
            except KeyError as exc:
                raise KeyError(f"Invalid mission type: {mission}") from exc

        for i in config["modules"]:
            self.modules.append(
                Module( i["pkg"], i["launch_file"], i["heartbeats_topic"], bool(i["is_node_msg"]))
            )
            self.get_logger().info(f"✅ Added module {i['pkg']} to the list of modules to launch")

        for idx, module in enumerate(self.modules):
            #rclpy.spin(module)
            self.add_node_callback(module)
            self.get_logger().info(f"✅🎉✅🎉✅🎉✅🎉✅🎉 Adding module And spinning it")
            module.launch()
       
    
#    def shutdown(self) -> None:
#        for module in self.modules:
#            module.shutdownmodule()
#            module.shutdownlaunchfile()

#        self.missionType = "Not Selected"
#        self.isLaunched = False
#        self.modules = []
#        self.get_logger().info("All modules have been shutdown and cleared from the list")
         

    def shutdown(self) -> None:
        self.get_logger().info("Shutting down func in missionLauncher...")

        for module in list(self.modules):  # Use list() to create a copy of the list for safe iteration
            self.get_logger().warn(f"Shutting down module: {module.pkg}")
            
            try:
                module.stop_monitoring_for_shutdown()
            except Exception as e:
                self.get_logger().error(f"Error stopping monitoring for module {module.pkg}: {e}")
            try:
                module.shutdownlaunchfile()
            except Exception as e:
                self.get_logger().error(f"Error shutting down launch file for module {module.pkg}: {e}")
            try:
                module.shutdownmodule()
            except Exception as e:
                self.get_logger().error(f"failed to destroy module node {module.pkg}: {e}")
            
        self.missionType = "Not Selected"
        self.isLaunched = False
        self.modules.clear()  # Clear the list of modules
        self.get_logger().info("All modules have been shutdown and cleared from the list")




    def loopClosure_trackdrive_callback(self, msg: Int16):
        if msg.data == 1:
            self.get_logger().info("🏁🏁🏁🏁🏁🏁 Loop closure detected in trackdrive mission")

            # 1. Find the 'simple_pure_pursuit' module in the list
            to_shutdown = None
            for module in self.modules:
                self.get_logger().info(f"Shutting down module: {module.pkg}")
                module.shutdownmodule()
                module.shutdownlaunchfile()
                self.modules.remove(module)
            else:
                self.get_logger().warn("Could not find 'simple_pure_pursuit' module to shut down")

            # self.get_logger().info("Launching new module(s) from trackDrive2.json")
            # config = self.openConfig("trackDrive2.json")
            # for i in config["modules"]:
            #     new_module = Module(
            #         i["pkg"],
            #         i["launch_file"],
            #         i["heartbeats_topic"],
            #         bool(i["is_node_msg"])
            #     )

            #     self.add_node_callback(new_module)      # Add to executor in a new thread
            #     # new_module.launchmodule()               # Launch it
            #     self.modules.append(new_module)         # Track it
            #     self.get_logger().info(f"✅ Launched module {new_module.pkg}")


    def isReady(self) -> bool:
        '''
        Checks if all modules are ready
        '''
        self.get_logger().info(f"called isready and no. of modules is {len(self.modules)}")  # Print module count
        if not self.modules:
            self.get_logger().info("ERROR: self.modules is EMPTY! No modules have been added.")
            return False  
        
        for module in self.modules:

            self.get_logger().info(f"Module {module.pkg} state: {module.state}")
            if module.hasHeartbeat and module.state not in (ModuleStateE.Ready, ModuleStateE.Running):
                self.get_logger().info(f"Module {module.pkg} is not ready (current state: {module.state})")
                return False  # Not ready

        return True  # All modules are ready






