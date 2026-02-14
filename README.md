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

## 2. Viewing Outputs

### Verify Topics
In a new terminal (don't forget to `source install/setup.bash`):

1. **Run bag file**
   ```bash
   ros2 bag play /testing_conemapping/testing_conemapping_0.db3
   ```
   This bag contains the topics necassary for doing mapping from a real SVO recording.
   You can use this singular bag for now but more will be added
   bag details: Circular track for 2 laps in sunlight

2. **Check for Global Map (SLAM Output):**
   ```bash
   ros2 topic echo /map/global_cones
   ```
   *Expectation:* You should see a list of landmarks with non-zero coordinates.

3. **Check Vehicle Pose:**
   ```bash
   ros2 topic echo /pose_republisher/pose
   ```

## 3. Configuration & Parameters

The system behavior is controlled by `src/SLAM_Camera/src/cone_mapping/config/cone_mapping_params.yaml`.

Key parameters:
- **`max_detection_range`**: Maximum distance to accept cones (default: 15.0m).
- **`max_cone_height_deviation`**: Maximum allowed height (z-axis) for cones in the map frame. Set to **2.0m** to handle coordinate frame offsets.
- **`observations_for_confirmation`**: How many times a cone must be seen to be confirmed.

