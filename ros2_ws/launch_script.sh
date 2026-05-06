#!/bin/bash

# ROS2 Multi-Node Launcher with Crash Detection
# Usage: ./launch_nodes.sh <node1> <node2> ...
# Available nodes: zed, perception, deep, logging, rosbag, centerline

set -e

# Create logging_debug directory
mkdir -p logging_debug

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Arrays to track processes
declare -a PIDS=()
declare -a NODE_NAMES=()

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down all nodes...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait a bit for graceful shutdown
    sleep 2
    
    # Force kill if still running
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}All nodes stopped.${NC}"
}

# Set trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Function to launch a node in background and track it
launch_node() {
    local node_name=$1
    shift
    local command="$@"
    
    echo -e "${GREEN}Launching $node_name...${NC}"
    echo "Command: $command"
    
    # Launch in background and capture PID
    bash -c "$command > logging_debug/${node_name}.txt 2>&1" &
    local pid=$!
    
    PIDS+=($pid)
    NODE_NAMES+=("$node_name")
    
    echo -e "${GREEN}Started $node_name with PID $pid${NC}"
    sleep 2  # Give it time to initialize
}

# Function to monitor processes
monitor_processes() {
    while true; do
        for i in "${!PIDS[@]}"; do
            pid="${PIDS[$i]}"
            node_name="${NODE_NAMES[$i]}"
            
            # Check if process is still running
            if ! kill -0 "$pid" 2>/dev/null; then
                echo -e "\n${RED}ERROR: $node_name (PID $pid) has crashed!${NC}"
                echo -e "${RED}Shutting down all nodes...${NC}"
                cleanup
                exit 1
            fi
        done
        sleep 1
    done
}

# Parse input arguments and determine launch order
NODES_TO_LAUNCH=()
HAS_ROSBAG=false
HAS_LOGGING=false
HAS_PERCEPTION=false
HAS_ZED=false
HAS_DEEP=false

if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No nodes specified${NC}"
    echo "Usage: $0 <node1> <node2> ..."
    echo "Available nodes: zed, perception, deep, logging, rosbag, centerline"
    exit 1
fi

# Check which nodes are requested
for arg in "$@"; do
    case "$arg" in
        zed)
            HAS_ZED=true
            ;;
        perception)
            HAS_PERCEPTION=true
            ;;
        deep)
            HAS_DEEP=true
            ;;
        logging)
            HAS_LOGGING=true
            ;;
        rosbag)
            HAS_ROSBAG=true
            ;;
        centerline)
            HAS_CENTERLINE=true
            ;;
        *)
            echo -e "${RED}Unknown node: $arg${NC}"
            echo "Available nodes: zed, perception, deep, logging, rosbag, centerline"
            exit 1
            ;;
    esac
 done

# Build launch order: rosbag -> logging -> zed, perception -> deep -> centerline
if [ "$HAS_ROSBAG" = true ]; then
    NODES_TO_LAUNCH+=("rosbag")
fi

if [ "$HAS_LOGGING" = true ]; then
    NODES_TO_LAUNCH+=("logging")
fi

if [ "$HAS_ZED" = true ]; then
    NODES_TO_LAUNCH+=("zed")
fi

if [ "$HAS_PERCEPTION" = true ]; then
    NODES_TO_LAUNCH+=("perception")
fi

if [ "$HAS_DEEP" = true ]; then
    NODES_TO_LAUNCH+=("deep")
fi

if [ "$HAS_CENTERLINE" = true ]; then
    NODES_TO_LAUNCH+=("centerline")
fi

# Launch nodes in order
for node in "${NODES_TO_LAUNCH[@]}"; do
    case "$node" in
        rosbag)
            launch_node "rosbag" \
                "ros2 bag record /zed/zed_node/obj_det/objects /perception_markers /topic2"
            ;;
        logging)
            launch_node "logging" \
                "ros2 launch logging_system logging_launch.py"
            ;;
        zed)
            # Launch ZED node first
            launch_node "zed_node" \
                "ros2 launch zed_display_rviz2 display_zed_cam.launch.py start_zed_node:=True camera_model:=zed2i"
            
            # Wait a bit longer for camera to initialize
            echo "Waiting for ZED camera to initialize..."
            sleep 3
            ;;
        perception)
            # launch perception package
            launch_node "perception_package" \
                "ros2 launch perception_zed_pkg perception_launch.py"
            ;;
        deep)
            launch_node "deep_learning" \
                "ros2 run planning_deep_learning dl_node"
            ;;
        centerline)
            launch_node "centerline" \
                "ros2 launch planning_centerline_calc planning_centerline_calc.launch.py"
            ;;
    esac
 done

echo -e "\n${GREEN}=== All nodes launched successfully ===${NC}"
echo "Monitoring processes for crashes..."
echo "Press Ctrl+C to stop all nodes"
echo ""

# Monitor all processes
monitor_processes