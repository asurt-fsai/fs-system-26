# Formula Student System (Run Guide)

This repository contains the SLAM + Perception stack + Deep_learning for the Formula Student driverless vehicle. This guide explains how to build, run, and visualize the system.

## Prerequisites

- **ROS 2 Humble** installed on Ubuntu 22.04 (or similar).
- `colcon` build tool installed (`sudo apt install python3-colcon-common-extensions`).
- **ZED SDK** and drivers installed (if using real camera).

## 1. Quick Start

### Build the System
Always build from the root of the workspace 

```bash

# Build the project package
colcon build --symlink-install

# Source the overlay
source install/setup.bash
```

### Run the System
Launch the integrated stack (Perception + SLAM + TF):

```bash
ros2 launch cone_mapping integrated_launch.py use_rviz:=true 
```
the integrated launch file contains the (Perception + SLAM) pipeline
Receieves, it automatically launches rviz with the topics needed:
- for POSE: /zed/zed_node/pose 
- for PERCEPTION: /perception/landmarks
Publishes:
/map/global_cones (The map itself)
/map/global_cones_markers (The map itself, but for rviz to visualize)
```bash
ros2 run planning_deep_learning dl_node
```
the node for running the Deep Learning pipeline
Receieves:
- for MAP: /map/global_cones_markers
- for POSE: /zed/zed_node/odom
- for FRAME: base_link
Publishes:
/topic2 (The path itself)

1. **Run bag file**
   ```bash
   ros2 bag play /slam_dl/test5_0.db3
   ```
   a zig zag like track was used in this bag,


## 2. Viewing Outputs

### Verify Topics
In a new terminal (don't forget to `source install/setup.bash`):

## 3. Configuration & Parameters

The system behavior is controlled by `src/SLAM_Camera/src/cone_mapping/config/cone_mapping_params.yaml`.

Key parameters:
- **`max_detection_range`**: Maximum distance to accept cones (default: 15.0m).
at the moment it will be around 500 (was for testing purposes)
- **`max_cone_height_deviation`**: Maximum allowed height (z-axis) for cones in the map frame. Set to **2.0m** to handle coordinate frame offsets.
- **`observations_for_confirmation`**: How many times a cone must be seen to be confirmed.

