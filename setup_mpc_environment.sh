#!/bin/bash
# Setup script for MPC Controller with Isaac Sim integration
# 
# NOTE: For most users, we recommend using launch_mpc_direct.sh instead,
# which doesn't require environment setup and package discovery.
#
# This script is useful for custom launching or debugging.

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up MPC Controller environment..."
echo "Workspace: $SCRIPT_DIR"

# Source ROS 2 base installation
echo "Sourcing ROS 2 Jazzy..."
source /opt/ros/jazzy/setup.bash

# Set up workspace prefix path for package discovery
export AMENT_PREFIX_PATH="$SCRIPT_DIR/install:$AMENT_PREFIX_PATH"
echo "AMENT_PREFIX_PATH set to: $AMENT_PREFIX_PATH"

# Set ROS_PACKAGE_PATH explicitly for package discovery
export ROS_PACKAGE_PATH="$SCRIPT_DIR/install/mpc_controller/share:$ROS_PACKAGE_PATH"
echo "ROS_PACKAGE_PATH set to: $ROS_PACKAGE_PATH"

# Set library path for HPIPM and BLASFEO solvers
export LD_LIBRARY_PATH="$SCRIPT_DIR/src/mpc_controller/src/install/lib:$LD_LIBRARY_PATH"
echo "LD_LIBRARY_PATH updated with HPIPM library path"

# Source the colcon workspace
echo "Sourcing colcon workspace..."
source "$SCRIPT_DIR/install/setup.bash"

echo "✓ Environment setup complete!"
echo ""
echo "You can now run:"
echo "  ros2 launch mpc_controller mpc_controller.launch.py use_rviz:=false"
echo ""
echo "Or directly run the node:"
echo "  ros2 run mpc_controller mpc_controller_node --ros-args --log-level info"
echo ""
echo "RECOMMENDED: Use the direct launcher instead:"
echo "  $SCRIPT_DIR/launch_mpc_direct.sh [--use-rviz]"
