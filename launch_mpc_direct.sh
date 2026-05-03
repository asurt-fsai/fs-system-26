#!/bin/bash
# Direct launcher for MPC Controller with Bicycle Simulator + RViz
# Usage:
#   ./launch_mpc_direct.sh                  # bicycle sim + MPC + no RViz
#   ./launch_mpc_direct.sh --use-rviz       # + RViz visualization
#   ./launch_mpc_direct.sh --no-sim         # MPC + visualizer only (e.g. real car)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source ROS 2
source /opt/ros/jazzy/setup.bash
source "$SCRIPT_DIR/install/setup.bash"

# Set up solver library paths (HPIPM + BLASFEO)
export LD_LIBRARY_PATH="$SCRIPT_DIR/src/mpc_controller/src/install/lib:$LD_LIBRARY_PATH"

echo "==================================="
echo "MPC + Bicycle Simulator Launcher"
echo "==================================="
echo "Workspace: $SCRIPT_DIR"
echo ""

# Parse arguments
USE_RVIZ=false
USE_SIM=true
LOG_LEVEL="info"
TRACK_CSV="$SCRIPT_DIR/track.csv"

while [[ $# -gt 0 ]]; do
  case $1 in
    --use-rviz)    USE_RVIZ=true;  shift ;;
    --no-sim)      USE_SIM=false;  shift ;;
    --track)       TRACK_CSV="$2"; shift 2 ;;
    --log-level)   LOG_LEVEL="$2"; shift 2 ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--use-rviz] [--no-sim] [--track /path/to.csv] [--log-level {debug|info|warn|error}]"
      exit 1
      ;;
  esac
done

PARAMS_DIR="$SCRIPT_DIR/install/mpc_controller/share/mpc_controller/config"

echo "  Log level : $LOG_LEVEL"
echo "  Simulator : $USE_SIM"
echo "  RViz      : $USE_RVIZ"
echo "  Track CSV : $TRACK_CSV"
echo ""

# Start ROS 2 daemon if needed
ros2 daemon status > /dev/null 2>&1 || ros2 daemon start

# ── [1] Bicycle Simulator ─────────────────────────────────────────────────
SIM_PID=""
if [ "$USE_SIM" = true ]; then
  echo "[1/4] Starting Bicycle Simulator..."
  "$SCRIPT_DIR/install/mpc_controller/lib/mpc_controller/bicycle_simulator" \
    --ros-args --log-level "$LOG_LEVEL" \
    -p track_csv_path:="$TRACK_CSV" \
    -p initial_v:=2.0 \
    -p v_max:=15.0 &
  SIM_PID=$!
  sleep 1
else
  echo "[1/4] Bicycle simulator disabled (--no-sim)"
fi

# ── [2] MPC Controller ────────────────────────────────────────────────────
echo "[2/4] Starting MPC Controller Node..."
"$SCRIPT_DIR/install/mpc_controller/lib/mpc_controller/mpc_controller_node" \
  --ros-args --log-level "$LOG_LEVEL" \
  -p model_path:="$PARAMS_DIR/model.json" \
  -p costs_path:="$PARAMS_DIR/cost.json" \
  -p bounds_path:="$PARAMS_DIR/bounds.json" \
  -p norm_path:="$PARAMS_DIR/normalization.json" \
  -p control_frequency:=20.0 \
  -p use_odom_steering:=true \
  -p csv_output_path:=/tmp/mpc_data.csv \
  --remap /odom:=/carmaker/Odometry \
  --remap /ackermann_cmd:=/ackr &
MPC_PID=$!
sleep 1

# ── [3] MPC Visualizer ────────────────────────────────────────────────────
echo "[3/4] Starting MPC Visualizer..."
"$SCRIPT_DIR/install/mpc_controller/lib/mpc_controller/mpc_visualizer" \
  --ros-args --log-level "$LOG_LEVEL" \
  -p r_inner:=1.5 \
  -p r_outer:=1.5 &
VIZ_PID=$!
sleep 1

# ── [4] RViz ─────────────────────────────────────────────────────────────
RVIZ_PID=""
if [ "$USE_RVIZ" = true ]; then
  echo "[4/4] Starting RViz..."
  RVIZ_CONFIG="$PARAMS_DIR/mpc_test.rviz"
  if [ -f "$RVIZ_CONFIG" ]; then
    # Unset GTK_PATH to prevent VS Code snap's GTK modules from loading
    # the wrong libpthread (snap/core20) which is incompatible with the system glibc
    GTK_PATH="" rviz2 -d "$RVIZ_CONFIG" &
    RVIZ_PID=$!
  else
    echo "  Warning: RViz config not found: $RVIZ_CONFIG"
    GTK_PATH="" rviz2 &
    RVIZ_PID=$!
  fi
else
  echo "[4/4] RViz disabled (run with --use-rviz to enable)"
fi

echo ""
echo "==================================="
echo "System Running"
echo "==================================="
echo ""
echo "Key topics:"
echo "  /path              — track centerline (bicycle sim publishes)"
echo "  /carmaker/Odometry — vehicle state    (bicycle sim publishes)"
echo "  /ackr              — Ackermann cmd     (MPC publishes)"
echo "  /mpc/predicted_path— MPC horizon       (MPC publishes)"
echo "  /mpc/track_markers — track + cones     (visualizer publishes)"
echo ""
echo "CSV debug log: /tmp/mpc_data.csv"
echo "Columns: time_s, x, y, theta, v, delta, acc, steering_cmd, s, lateral_error, solve_time_ms"
echo ""
echo "Press Ctrl+C to stop all nodes."
echo ""

# Cleanup on exit
cleanup() {
  echo ""
  echo "Stopping all nodes..."
  [ -n "$SIM_PID"  ] && kill "$SIM_PID"  2>/dev/null || true
  [ -n "$MPC_PID"  ] && kill "$MPC_PID"  2>/dev/null || true
  [ -n "$VIZ_PID"  ] && kill "$VIZ_PID"  2>/dev/null || true
  [ -n "$RVIZ_PID" ] && kill "$RVIZ_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

wait


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
