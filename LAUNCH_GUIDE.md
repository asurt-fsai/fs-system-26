# MPC Controller Launch Guide

## Quick Start

### Option 1: Direct Launcher (Recommended)
The simplest way to run the MPC Controller with Isaac Sim integration:

```bash
cd /home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26
./launch_mpc_direct.sh [--use-rviz] [--log-level {debug|info|warn|error}]
```

**Examples:**
```bash
# Start with RViz visualization
./launch_mpc_direct.sh --use-rviz

# Start with debug logging
./launch_mpc_direct.sh --log-level debug

# Both options
./launch_mpc_direct.sh --use-rviz --log-level info
```

### Option 2: Using setup_mpc_environment.sh
For more control or custom configurations:

```bash
cd /home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26
source ./setup_mpc_environment.sh

# Then run the node directly
ros2 run mpc_controller mpc_controller_node --ros-args --log-level info

# Or run the visualizer
ros2 run mpc_controller mpc_visualizer --ros-args --log-level info
```

## System Requirements

- **ROS 2 Jazzy** installed at `/opt/ros/jazzy/`
- **HPIPM/BLASFEO** solver libraries pre-built in workspace
- **Isaac Sim** (or any ROS 2-compatible simulator) publishing:
  - `/odom` (nav_msgs/Odometry) — vehicle state feedback
  - `/joint_states` (sensor_msgs/JointState) — steering angle feedback

## Topics

### Subscriptions
| Topic | Type | Description |
|-------|------|-------------|
| `/path` | nav_msgs/Path | Reference trajectory waypoints |
| `/odom` | nav_msgs/Odometry | Vehicle pose and velocity |
| `/joint_states` | sensor_msgs/JointState | Steering joint angles |
| `/clock` | rosgraph_msgs/Clock | Simulation time |

### Publications
| Topic | Type | Description |
|-------|------|-------------|
| `/ackermann_cmd` | ackermann_msgs/AckermannDriveStamped | Steering + acceleration commands |
| `/visualization_marker_array` | visualization_msgs/MarkerArray | RViz track visualization |

## Parameters

All parameters are passed through the launch system or environment. Key parameters:

- `control_dt` (float, default 0.05): Control loop time step [seconds]
- `model_path`: Path to vehicle model JSON
- `costs_path`: Path to cost parameters JSON  
- `bounds_path`: Path to constraints JSON
- `norm_path`: Path to normalization factors JSON

## Troubleshooting

### "Package 'mpc_controller' not found"
**Issue:** ROS 2 cannot discover the mpc_controller package
**Solution:** Use the direct launcher (`./launch_mpc_direct.sh`) instead, which bypasses ros2 package discovery

### "libhpipm.so: cannot open shared object"
**Issue:** HPIPM solver library not found
**Solution:** Ensure LD_LIBRARY_PATH includes solver install directory:
```bash
export LD_LIBRARY_PATH="/path/to/fs-system-26/src/mpc_controller/src/install/lib:$LD_LIBRARY_PATH"
```

### "Could not open params/model.json"
**Issue:** Parameter files not found
**Solution:** Ensure config files are in `src/mpc_controller/config/` or install them properly via colcon

### "Waiting for /path reference trajectory..."
**Info:** Normal behavior when simulator hasn't published a path yet
**Action:** Publish a path message from Isaac Sim or a test script

## Control Loop Details

The MPC controller runs at 100 Hz and implements:

1. **State Feedback**: Reads `/odom` and `/joint_states` at each cycle
2. **MPC Optimization**: Solves optimal control problem using HPIPM (3 iterations)
3. **Integration Layer**: Converts MPC rate outputs to reference commands with physical limits
4. **Command Publication**: Publishes control commands to `/ackermann_cmd`

Control sequence:
```
[100 Hz Timer] → [Read State] → [Run MPC] → [Integration Layer] → [Publish Commands]
```

## Files and Structure

- **Launchers:**
  - `launch_mpc_direct.sh` - Direct node launcher (recommended)
  - `setup_mpc_environment.sh` - Environment setup script
  - `src/mpc_controller/launch/mpc_controller.launch.py` - ROS 2 launch file

- **Source Code:**
  - `src/mpc_controller/src/IPG\ Node/mpc_controller_node.cpp` - Main ROS 2 node
  - `src/mpc_controller/src/IPG\ Node/mpc_visualizer.cpp` - RViz visualizer
  - `src/mpc_controller/src/MPC/mpc.cpp` - MPC solver wrapper

- **Configuration:**
  - `src/mpc_controller/config/model.json` - Vehicle model parameters
  - `src/mpc_controller/config/cost.json` - MPC cost weights
  - `src/mpc_controller/config/bounds.json` - Control constraints
  - `src/mpc_controller/config/normalization.json` - State normalization (optional)
  - `src/mpc_controller/config/mpc_test.rviz` - RViz display config

## Advanced: Manual Environment Setup

If you need more control over the environment:

```bash
#!/bin/bash
WORKSPACE_DIR="/home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26"

# Source ROS 2
source /opt/ros/jazzy/setup.bash

# Set environment
export AMENT_PREFIX_PATH="$WORKSPACE_DIR/install:/opt/ros/jazzy"
export LD_LIBRARY_PATH="$WORKSPACE_DIR/src/mpc_controller/src/install/lib:$LD_LIBRARY_PATH"
export ROS_PACKAGE_PATH="$WORKSPACE_DIR/install/mpc_controller/share:$ROS_PACKAGE_PATH"

# Run node
"$WORKSPACE_DIR/install/mpc_controller/lib/mpc_controller/mpc_controller_node"
```

## Integration with Isaac Sim

1. **Set Up ROS 2 Bridge** in Isaac Sim to publish:
   - Odometry to `/odom`
   - Joint states to `/joint_states`

2. **Publish Reference Path**:
   ```python
   import rclpy
   from nav_msgs.msg import Path, PathPoint
   from geometry_msgs.msg import Pose
   
   node = rclpy.create_node('path_publisher')
   pub = node.create_publisher(Path, '/path', 10)
   
   msg = Path()
   msg.header.frame_id = 'base_link'
   # Add waypoints...
   pub.publish(msg)
   ```

3. **Verify** `/ackermann_cmd` commands are received by Isaac Sim's vehicle controller

## Performance Targets

- **Control Frequency:** 100 Hz (10 ms cycle time)
- **MPC Solver Time:** ~2-3 ms (with HPIPM)
- **End-to-End Latency:** <10 ms (typically 5-8 ms)

Monitor with:
```bash
ros2 topic hz /ackermann_cmd     # Check publish rate
ros2 topic echo /ackermann_cmd   # Inspect commands
rqt_graph                        # Visualize node graph
```
