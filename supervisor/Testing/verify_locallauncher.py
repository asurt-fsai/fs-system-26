#!/usr/bin/env python3
"""
Simple verification script to see if LocalLauncher works
"""

import sys
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading


from supervisor.helpers.Module.LocalLuncher import LocalLauncher
from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Module.ModuleState import ModuleState

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

class SimpleCommunication:
    def __init__(self):
        self.module = None
        rclpy.init()
        self._ros_node = Node('supervisor_comm')
        self._sub = self._ros_node.create_subscription(
            String,
            '/heartbeat',
            self._on_heartbeat_msg,
            10
        )
        # Spin in background thread
        self._thread = threading.Thread(target=rclpy.spin, args=(self._ros_node,), daemon=True)
        self._thread.start()
        print("✓ ROS subscriber started on /heartbeat")

    def _on_heartbeat_msg(self, msg):
        print(f"✓ Real heartbeat received: {msg.data}")
        if self.module:
            self.module.on_heartbeat()

    def register_module(self, module):
        self.module = module
        print("✓ Module registered")

print("\n" + "="*50)
print("TESTING LOCALLAUNCHER WITH SIMPLE NODE")
print("="*50)


# Create instances
comm = SimpleCommunication()
launcher = LocalLauncher()


# If you created your own package, change these values
module = Module(
    pkg="test_node",  
    launch_file="test_launch.py",  
    communication=comm,
    launcher=launcher,
    heartbeat_timeout=3.0  # 3 second timeout for faster testing
)

print(f"\n1. Launching module...")
success = module.launch()
time.sleep(2)

if success and module.process:
    print(f"   ✓ Module launched with PID: {module.process.pid}")
else:
    print("   ✗ Launch failed!")
    sys.exit(1)


print(f"\n2. Waiting for real heartbeats from ROS topic ...")
for i in range(12):
    time.sleep(1)
    print(f"   t+{i+1}s: module state: {module.state}, lastHeartbeat: {time.time() - module.lastHeartbeatTime:.1f}s ago")


print(f"\n3. Stopping heartbeats - waiting for heartbeat timeout and restart...")
baseline_pid = getattr(module.process, 'pid', None)
deadline = time.time() + 8
detected = False

while time.time() < deadline:
    time.sleep(1)
    module.check_health()
    print(f"   state: {module.state}")
    if module.lastRestartTime > 0 and module.process and module.process.pid != baseline_pid:
        print(f"   ✓ Heartbeat timeout detected → restarted with new PID: {module.process.pid}")
        detected = True
        break

if not detected:
    print(f"   ✗ Heartbeat timeout or restart not detected (state={module.state})")


print(f"\n4. Module should restart automatically...")
time.sleep(5)  # Wait for restart

if module.process:
    print(f"   ✓ Module restarted with new PID: {module.process.pid}")
else:
    print("   ✗ Restart failed!")

print(f"\n5. Shutting down module...")
module.shutdown()
time.sleep(2)

if module.process is None:
    print("   ✓ Module shutdown successfully")
else:
    print("   ✗ Shutdown failed!")

print("\n" + "="*50)
print("TEST COMPLETE")
print("="*50)