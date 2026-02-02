#!/bin/bash

# Source ROS 2 and workspace
source /opt/ros/humble/setup.bash  # Change 'humble' to your ROS 2 distro if different
source /home/amremad2210/Documents/Formula_AI/FSAI_26/fs-system-26/Perception/ros2_ws/install/setup.bash



# Generate timestamp for unique bag and log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BAG_DIR="test_bag_${TIMESTAMP}"
LOG_FILE_PATH="test_log_${TIMESTAMP}.txt"

# Step 1: Launch the ZED camera with RViz
echo "Launching ZED camera..."
ros2 launch zed_display_rviz2 display_zed_cam.launch.py camera_model:=zed2i &
ZED_PID=$!
echo "ZED camera launched with PID $ZED_PID"

# Wait for the ZED camera to initialize
echo "Waiting for camera to initialize..."
sleep 15

# Step 2: Start recording ROS2 bag (all topics)
echo "Starting ROS2 bag recording..."
ros2 bag record -o "$BAG_DIR" /zed/zed_node/obj_det/objects &
BAG_PID=$!
echo "ROS2 bag recording started with PID $BAG_PID to directory $BAG_DIR"

# Record for a specific duration or wait for user to stop
# Adjust the sleep duration as needed, or comment out to manually stop with Ctrl+C
echo "Recording for 60 seconds... (Press Ctrl+C to stop earlier)"
sleep 60

# Stop the bag recording
kill $BAG_PID
wait $BAG_PID 2>/dev/null
echo "ROS2 bag recording stopped"

# Kill the ZED camera process and RViz
echo "Shutting down ZED camera and RViz..."
kill $ZED_PID
wait $ZED_PID 2>/dev/null
killall -9 rviz2

rm -rf /dev/shm/fastrtps_*
rm -rf /dev/shm/sem.fastrtps_*

# Step 3: Extract object detection messages from bag to log file
# echo "Extracting object detection data from bag to log file..."
# ros2 bag play "$BAG_DIR" &
# PLAY_PID=$!
# sleep 5

# # Echo topic to log file during playback
# timeout 20 ros2 topic echo /zed/zed_node/obj_det/objects > "$LOG_FILE_PATH" &
# ECHO_PID=$!

# # Wait for playback to complete
# wait $PLAY_PID 2>/dev/null
# wait $ECHO_PID 2>/dev/null

# echo "Object Detection Logger Node Done"

# # Step 4: Run the test analysis script (uncomment when ready)
# #python3 test_analysis.py "$LOG_FILE_PATH"

# # Notify the user that the script has completed
# echo "Test run and analysis completed."
# echo "ROS2 bag saved in: $BAG_DIR"
# echo "Results are saved in $LOG_FILE_PATH"