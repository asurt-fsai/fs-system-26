# Formula Student System (Run Guide)

This repository contains the SLAM and perception stack for the Formula Student driverless vehicle. This guide explains how to build, run, and visualize the system.

## Prerequisites

- **ROS 2 Humble** installed on Ubuntu 22.04 (or similar).
- `colcon` build tool installed (`sudo apt install python3-colcon-common-extensions`).
- **ZED SDK** and drivers installed (if using real camera).

## 1. Quick Start

### Build the System
Always build from the root of the workspace (`fs-system-26/`):

```bash
# Sourcing ROS 2 first (if not in .bashrc)
source /opt/ros/humble/setup.bash

# Build the project package
colcon build --symlink-install

# Source the overlay
source install/setup.bash
```

### Run the System
Launch the integrated stack (Perception + SLAM + TF):

```bash
ros2 launch cone_mapping integrated_launch.py
```
### Run the System (using rviz)
Launch the integrated stack (Perception + SLAM + TF):

```bash
ros2 launch cone_mapping integrated_launch.py use_rviz:=true
```
*Note: In order to see pose + map together, you must add both the pose coming from the zed topic and the markerArray coming from the map inside of rviz.
Don't also forget to set the fixed frame to "map" to see the visualization

## 2. Viewing Outputs

### Verify Topics
In a new terminal (don't forget to `source install/setup.bash`):

1. **Run bag file**
   ```bash
   ros2 bag play [bag_file_path.db3]
   ```

2. **Check for Global Map (SLAM Output):**
   ```bash
   ros2 topic echo /map/global_cones
   ```
   *Expectation:* You should see a list of landmarks with non-zero coordinates.

2. **Check for Visualization Markers:**
   ```bash
   ros2 topic echo /map/global_cones_markers
   ```
   *Note: Add a "MarkerArray" display in RViz subscribed to this topic to see 3D cones.*

3. **Check for Raw Detections:**
   ```bash
   ros2 topic echo /perception/landmarks
   ```

4. **Check Vehicle Pose:**
   ```bash
   ros2 topic echo /pose_republisher/pose
   ```

## 3. Configuration & Parameters

The system behavior is controlled by `src/SLAM_Camera/src/cone_mapping/config/cone_mapping_params.yaml`.

Key parameters:
- **`max_detection_range`**: Maximum distance to accept cones (default: 15.0m).
- **`max_cone_height_deviation`**: Maximum allowed height (z-axis) for cones in the map frame. Set to **2.0m** to handle coordinate frame offsets.
- **`observations_for_confirmation`**: How many times a cone must be seen to be confirmed.

