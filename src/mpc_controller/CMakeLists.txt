cmake_minimum_required(VERSION 3.8)
project(mpc_controller)

# Compiler settings
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(casadi REQUIRED)

# Include directories
include_directories(
  include
  ${EIGEN3_INCLUDE_DIR}
)

# Create library
add_library(mpc_lib
  src/Params/params.cpp
  src/config.cpp
  src/types.cpp
  "src/Bicycle Model/bicycle_model.cpp"
  src/MPC/mpc_solver.cpp
  src/Constraints/constraints.cpp
  src/Constraints/trackConstraints.cpp
  src/Constraints/boxConstraints.cpp
  src/Integrator/integration_methods.cpp
  src/Cost/cost.cpp
  src/Spline/Arc_Spline.cpp
  src/Spline/Cubic_Spline.cpp
)

target_link_libraries(mpc_lib
  Eigen3::Eigen
  casadi
)

# Create ROS 2 node
add_executable(mpc_controller_node
  "src/IPG Node/mpc_controller_node.cpp"
)

target_link_libraries(mpc_controller_node
  mpc_lib
  ${rclcpp_LIBRARIES}
)

ament_target_dependencies(mpc_controller_node
  rclcpp
  std_msgs
  geometry_msgs
  nav_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

# Install
install(TARGETS mpc_controller_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

# Export
ament_export_include_directories(include)
ament_export_libraries(mpc_lib)
ament_export_dependencies(rclcpp std_msgs geometry_msgs nav_msgs tf2 tf2_ros Eigen3 casadi)

ament_package()
