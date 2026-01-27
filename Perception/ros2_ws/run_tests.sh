#!/bin/bash

# Source ROS 2 and workspace
source /opt/ros/humble/setup.bash  # Change 'humble' to your ROS 2 distro if different
source /home/amremad2210/ros2_ws/install/setup.bash

# Generate timestamp for unique log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE_PATH="test_log_${TIMESTAMP}.txt"

# Step 1: Launch the ZED camera with RViz
echo "Launching ZED camera..."
ros2 launch zed_display_rviz2 display_zed_cam.launch.py camera_model:=zed2i &
ZED_PID=$!
echo "ZED camera launched with PID $ZED_PID"

# Wait for the ZED camera to initialize
echo "Waiting for camera to initialize..."
sleep 15

# Step 2: Run the ROS2 node to subscribe to the object detection topic and log messages
echo "Launching Object Detection Logger Node"
python3 /home/amremad2210/ros2_ws/src/log_object_detection.py "$LOG_FILE_PATH"
echo "Object Detection Logger Node Done"

#ros2 topic echo /zed/zed_node/obj_det/objects >> "$LOG_FILE_PATH" 

# Kill the ZED camera process
echo "Shutting down ZED camera..."
kill $ZED_PID
wait $ZED_PID 2>/dev/null

# Step 3: Run the test analysis script
#python3 test_analysis.py "$LOG_FILE_PATH"

# Notify the user that the script has completed
echo "Test run and analysis completed. Results are saved in $LOG_FILE_PATH"