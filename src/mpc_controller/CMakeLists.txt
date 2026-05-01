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
find_package(ackermann_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(Eigen3 REQUIRED)
# Note: casadi removed — MPC uses HPIPM/BLASFEO, not CasADi

# Include directories
include_directories(
  include
  ${EIGEN3_INCLUDE_DIR}
)

# Locate pre-built BLASFEO (from build_solver.sh output or source build)
# Optional overrides for moved/copied workspaces:
#   export MPC_SOLVER_INSTALL=/absolute/path/to/src/install
#   export MPC_SOLVER_BUILD=/absolute/path/to/src/build_solver/blasfeo
set(BLASFEO_BUILD_DIR "$ENV{MPC_SOLVER_BUILD}")
if(NOT BLASFEO_BUILD_DIR)
  set(BLASFEO_BUILD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/build_solver/blasfeo")
endif()

set(BLASFEO_INSTALL "$ENV{MPC_SOLVER_INSTALL}")
if(NOT BLASFEO_INSTALL)
  set(BLASFEO_INSTALL "${CMAKE_CURRENT_SOURCE_DIR}/src/install")
endif()

message(STATUS "BLASFEO build dir: ${BLASFEO_BUILD_DIR}")
message(STATUS "Solver install dir: ${BLASFEO_INSTALL}")
if(EXISTS "${BLASFEO_INSTALL}/lib/libblasfeo.so")
  set(BLASFEO_LIB       "${BLASFEO_INSTALL}/lib/libblasfeo.so")
  set(BLASFEO_INCLUDE   "${BLASFEO_INSTALL}/include")
elseif(EXISTS "${BLASFEO_BUILD_DIR}/libblasfeo.so")
  set(BLASFEO_LIB       "${BLASFEO_BUILD_DIR}/libblasfeo.so")
  set(BLASFEO_INCLUDE   "${CMAKE_CURRENT_SOURCE_DIR}/src/blasfeo/include")
else()
  set(BLASFEO_LIB       "")
  set(BLASFEO_INCLUDE   "${CMAKE_CURRENT_SOURCE_DIR}/src/blasfeo/include")
endif()

# Locate HPIPM (optional)
find_library(HPIPM_LIB hpipm
    HINTS "${BLASFEO_INSTALL}/lib" /usr/local/lib /usr/lib
    NO_DEFAULT_PATH)
if(HPIPM_LIB)
  set(HPIPM_INCLUDE "${BLASFEO_INSTALL}/include")
  message(STATUS "HPIPM found at ${HPIPM_LIB}")
  message(STATUS "HPIPM headers at ${HPIPM_INCLUDE}")
else()
  message(STATUS "HPIPM library not found - using stubs only")
  set(HPIPM_INCLUDE "${CMAKE_CURRENT_SOURCE_DIR}/src/hpipm_stubs")
endif()

# Include directories
include_directories(
  include
  src
  "src/IPG Node"
  ${EIGEN3_INCLUDE_DIR}
  ${BLASFEO_INCLUDE}
  ${HPIPM_INCLUDE}
  ${CMAKE_CURRENT_SOURCE_DIR}/src/hpipm-cpp-main/include
)

# Create library — only list source files that exist
add_library(mpc_lib
  src/Params/params.cpp
  src/config.cpp
  src/types.cpp
  "src/Bicycle Model/bicycle_model.cpp"
  src/MPC/mpc.cpp
  src/Constraints/constraints.cpp
  src/Constraints/trackConstraints.cpp
  src/Integrator/integration_methods.cpp
  src/Cost/cost.cpp
  src/Spline/Arc_Spline.cpp
  src/Spline/Cubic_Spline.cpp
  src/Interfaces/solver_interface.cpp
  src/Interfaces/hpipm_interface.cpp
)

set(MPC_LINK_LIBS Eigen3::Eigen)
if(BLASFEO_LIB)
  list(APPEND MPC_LINK_LIBS ${BLASFEO_LIB})
  message(STATUS "Linking BLASFEO: ${BLASFEO_LIB}")
endif()
if(HPIPM_LIB)
  list(APPEND MPC_LINK_LIBS ${HPIPM_LIB})
  message(STATUS "Linking HPIPM: ${HPIPM_LIB}")

  # Build hpipm-cpp C++ wrapper sources alongside mpc_lib when HPIPM is
  # available.  The wrapper files must not see N/NX/NU macros from config.h,
  # so they are compiled as a separate static library that is linked in.
  set(HPIPM_CPP_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/hpipm-cpp-main/src")
  add_library(hpipm_cpp_wrapper STATIC
    ${HPIPM_CPP_SRC_DIR}/detail/d_ocp_qp_dim_wrapper.cpp
    ${HPIPM_CPP_SRC_DIR}/detail/d_ocp_qp_wrapper.cpp
    ${HPIPM_CPP_SRC_DIR}/detail/d_ocp_qp_sol_wrapper.cpp
    ${HPIPM_CPP_SRC_DIR}/detail/d_ocp_qp_ipm_arg_wrapper.cpp
    ${HPIPM_CPP_SRC_DIR}/detail/d_ocp_qp_ipm_ws_wrapper.cpp
    ${HPIPM_CPP_SRC_DIR}/ocp_qp_dim.cpp
    ${HPIPM_CPP_SRC_DIR}/ocp_qp_ipm_solver_settings.cpp
    ${HPIPM_CPP_SRC_DIR}/ocp_qp_ipm_solver_statistics.cpp
    ${HPIPM_CPP_SRC_DIR}/ocp_qp_ipm_solver.cpp
  )
  target_include_directories(hpipm_cpp_wrapper PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/hpipm-cpp-main/include
    ${BLASFEO_INCLUDE}
    ${HPIPM_INCLUDE}
    ${EIGEN3_INCLUDE_DIR}
  )
  target_link_libraries(hpipm_cpp_wrapper
    ${BLASFEO_LIB}
    ${HPIPM_LIB}
    Eigen3::Eigen
  )
  list(APPEND MPC_LINK_LIBS hpipm_cpp_wrapper)
  message(STATUS "Building hpipm-cpp C++ wrapper library")
endif()

target_link_libraries(mpc_lib ${MPC_LINK_LIBS})

# Add HPIPM compile definition if library found
if(HPIPM_LIB)
  target_compile_definitions(mpc_lib PRIVATE HPIPM_CPP_AVAILABLE)
  message(STATUS "HPIPM_CPP_AVAILABLE enabled")
endif()

# Create ROS 2 node — MPC Controller (IPG + RViz test)
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
  ackermann_msgs
  nav_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

# ── MPC Visualizer Node (shared by IPG and RViz test) ────────────────────
add_executable(mpc_visualizer
  "src/IPG Node/mpc_visualizer.cpp"
  "src/IPG Node/mpc_visualizer_main.cpp"
)

target_link_libraries(mpc_visualizer
  ${rclcpp_LIBRARIES}
)

ament_target_dependencies(mpc_visualizer
  rclcpp
  std_msgs
  geometry_msgs
  nav_msgs
  visualization_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

# ── Install targets ────────────────────────────────────────────────────────
install(TARGETS
  mpc_controller_node
  mpc_visualizer
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install config files (JSON params + RViz config)
install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)
install(DIRECTORY src/Params/
  DESTINATION share/${PROJECT_NAME}/config
  FILES_MATCHING PATTERN "*.json"
)

# Install track.csv data file
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../track.csv")
  install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../../track.csv"
    DESTINATION share/${PROJECT_NAME}/config
  )
  message(STATUS "track.csv found — will be installed to config/")
else()
  message(STATUS "track.csv not found at workspace root — skipping")
endif()

# Export
ament_export_include_directories(include)
ament_export_libraries(mpc_lib)
ament_export_dependencies(rclcpp std_msgs geometry_msgs nav_msgs visualization_msgs tf2 tf2_ros Eigen3)

ament_package()
