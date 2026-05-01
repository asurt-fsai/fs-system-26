#!/bin/bash
# Direct launcher for MPC Controller
# Bypasses ros2 launch infrastructure for testing when package discovery fails

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source ROS 2
source /opt/ros/jazzy/setup.bash

# Set up environment
export AMENT_PREFIX_PATH="$SCRIPT_DIR/install:/opt/ros/jazzy"
export LD_LIBRARY_PATH="$SCRIPT_DIR/src/mpc_controller/src/install/lib:$LD_LIBRARY_PATH"

echo "==================================="
echo "MPC Controller Launcher"
echo "==================================="
echo "Workspace: $SCRIPT_DIR"
echo ""

# Parse arguments
USE_RVIZ=false
LOG_LEVEL="info"

while [[ $# -gt 0 ]]; do
  case $1 in
    --use-rviz)
      USE_RVIZ=true
      shift
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--use-rviz] [--log-level {debug|info|warn|error}]"
      exit 1
      ;;
  esac
done

echo "Starting MPC Controller..."
echo "  Log level: $LOG_LEVEL"
echo "  RViz: $USE_RVIZ"
echo ""

# Start ROS master (daemon)
if ! ros2 daemon status > /dev/null 2>&1; then
  echo "Starting ROS 2 daemon..."
  ros2 daemon start
fi

# Launch the mpc_controller_node
echo "[1/3] Starting MPC Controller Node..."
"$SCRIPT_DIR/install/mpc_controller/lib/mpc_controller/mpc_controller_node" \
  --ros-args --log-level "$LOG_LEVEL" &
MPC_PID=$!
sleep 1

# Launch the mpc_visualizer
echo "[2/3] Starting MPC Visualizer..."
"$SCRIPT_DIR/install/mpc_controller/lib/mpc_controller/mpc_visualizer" \
  --ros-args --log-level "$LOG_LEVEL" &
VIZ_PID=$!
sleep 1

# Launch RViz if requested
if [ "$USE_RVIZ" = true ]; then
  echo "[3/3] Starting RViz..."
  RVIZ_CONFIG="$SCRIPT_DIR/src/mpc_controller/config/mpc_test.rviz"
  if [ -f "$RVIZ_CONFIG" ]; then
    rviz2 -d "$RVIZ_CONFIG" &
    RVIZ_PID=$!
  else
    echo "Warning: RViz config not found at $RVIZ_CONFIG"
  fi
else
  echo "[3/3] RViz disabled"
fi

echo ""
echo "==================================="
echo "✓ MPC Controller Running"
echo "==================================="
echo ""
echo "Topics:"
echo "  Subscribe:  /path (nav_msgs/Path), /odom (nav_msgs/Odometry), /joint_states (sensor_msgs/JointState)"
echo "  Publish:    /ackermann_cmd (ackermann_msgs/AckermannDriveStamped)"
echo ""
echo "Press Ctrl+C to stop..."
echo ""

# Wait for all processes
trap "kill $MPC_PID $VIZ_PID $RVIZ_PID 2>/dev/null; exit 0" INT TERM

wait
