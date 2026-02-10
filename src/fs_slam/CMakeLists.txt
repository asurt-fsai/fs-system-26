cmake_minimum_required(VERSION 3.8)
project(fs_slam)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# --- 1. FIND ALL DEPENDENCIES ---
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# [NEW] Dependencies for the new listener
find_package(fs_interfaces REQUIRED)   # To read LandmarkArray
find_package(asurt_msgs REQUIRED)      # Landmark array messages
find_package(zed_msgs REQUIRED)  # To read ZED Objects (if needed)

# --- 2. GENERATE INTERNAL MESSAGES (Legacy/Internal) ---
# NOTE: Cone.msg and ConeArray.msg files do not exist, so skipping message generation
# If you need these messages, create msg/Cone.msg and msg/ConeArray.msg files

# --- 3. BUILD THE NODES ---

# Node B: Perception Listener
add_executable(perception_listener src/perception_listener.cpp)
ament_target_dependencies(perception_listener
  rclcpp
  std_msgs
  sensor_msgs
  fs_interfaces   # Links the Landmark messages
  asurt_msgs      # Landmark array messages
  zed_msgs  # Links the ZED object messages
)

# --- 4. INSTALL RULES ---
install(TARGETS 
  perception_listener  # Installs the listener executable
  DESTINATION lib/${PROJECT_NAME}
)

# --- 5. TESTING ---
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()