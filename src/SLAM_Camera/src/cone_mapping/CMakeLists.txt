cmake_minimum_required(VERSION 3.8)
project(cone_mapping)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
#find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(message_filters REQUIRED)

# Generate messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Landmark.msg"
  "msg/LandmarkArray.msg"
  DEPENDENCIES std_msgs geometry_msgs
)

# Install Python modules
#ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  cone_mapping/cone_mapping_node.py
  cone_mapping/test_case_1_ideal.py
  cone_mapping/test_case_2_noisy.py
  cone_mapping/test_case_3_loop_closure.py
  cone_mapping/test_case_5_multilap.py
  DESTINATION lib/${PROJECT_NAME}
)
# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

# Install message files
install(DIRECTORY
  msg
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
