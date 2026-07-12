cmake_minimum_required(VERSION 3.5)
project(ros_can)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(std_srvs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(ackermann_msgs REQUIRED)
find_package(eufs_msgs REQUIRED)

# =========================================================================
# CHANGED: Removed the buggy external 'add_custom_target' Makefile runner
# and replaced it with a native CMake static library compilation.
# =========================================================================
add_library(fs_ai_api STATIC 
    FS-AI-API/FS-AI_API/fs-ai_api.c
    FS-AI-API/FS-AI_API/can.c
)
# Force Position Independent Code (vital for mixing C libraries with ROS 2 on ARM)
set_target_properties(fs_ai_api PROPERTIES POSITION_INDEPENDENT_CODE ON)
# =========================================================================

# Create ros_can_node executable
include_directories(include FS-AI-API/FS-AI_API)
add_executable(ros_can_node src/ros_can.cpp)

# =========================================================================
# CHANGED: Removed 'add_dependencies(ros_can_node fs-ai-api)' 
# and updated target_link_libraries to point to our native CMake target 
# plus the threading library.
# =========================================================================
target_link_libraries(ros_can_node fs_ai_api pthread)
# =========================================================================

ament_target_dependencies(ros_can_node rclcpp tf2 tf2_ros std_srvs sensor_msgs std_msgs ackermann_msgs eufs_msgs)

# Install executable
install(TARGETS ros_can_node
    DESTINATION lib/${PROJECT_NAME}
)

# Install launch files.
install(DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}/
)

ament_package()
