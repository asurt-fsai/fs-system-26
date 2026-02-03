cmake_minimum_required(VERSION 3.8)
project(fs_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Find dependencies for MESSAGE GENERATION
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# 2. Generate the messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Landmark.msg"
  "msg/LandmarkArray.msg"
  DEPENDENCIES geometry_msgs std_msgs
)

# 3. Export dependencies
ament_export_dependencies(rosidl_default_runtime)

ament_package()