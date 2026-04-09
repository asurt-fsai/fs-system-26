################################################################################
# CMakeLists.txt for MPC Solver with BLASFEO/HPIPM
#
# This CMakeLists.txt integrates the optimized BLASFEO and HPIPM libraries
# built from build_solver.sh into the MPC controller project.
#
# Usage:
#   mkdir build && cd build
#   cmake ..
#   make -j$(nproc)
################################################################################

cmake_minimum_required(VERSION 3.10)

project(MPCController
    VERSION 1.0.0
    DESCRIPTION "Model Predictive Control with HPIPM Solver"
    LANGUAGES CXX C
)

################################################################################
# Project Configuration
################################################################################

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O3 -march=native")

# Option to use pre-built solver
set(USE_PREBUILT_SOLVER OFF CACHE BOOL "Use pre-built BLASFEO/HPIPM from build_solver.sh")

################################################################################
# Include Pre-built Solver Configuration (if available)
################################################################################

set(SOLVER_CONFIG_FILE "${CMAKE_CURRENT_SOURCE_DIR}/solver_build_config.cmake")

if(EXISTS "${SOLVER_CONFIG_FILE}")
    message(STATUS "Loading solver build configuration from ${SOLVER_CONFIG_FILE}")
    include("${SOLVER_CONFIG_FILE}")
    set(USE_PREBUILT_SOLVER ON)
else()
    message(STATUS "Solver build config not found. Using system or fallback BLASFEO/HPIPM")
endif()

################################################################################
# Find or Use Pre-built Dependencies
################################################################################

# BLASFEO
if(USE_PREBUILT_SOLVER AND DEFINED BLASFEO_DIR)
    message(STATUS "Using pre-built BLASFEO from: ${BLASFEO_DIR}")
    set(BLASFEO_INCLUDE_DIRS "${BLASFEO_DIR}/include")
    set(BLASFEO_LIBRARIES "${BLASFEO_DIR}/lib/libblasfeo.so")
else()
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(BLASFEO blasfeo)
    endif()
    
    if(NOT BLASFEO_FOUND)
        message(WARNING "BLASFEO not found. Using fallback stubs only (no actual solver)")
        set(BLASFEO_INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/blasfeo/include")
        set(BLASFEO_LIBRARIES "")
    endif()
endif()

# HPIPM
if(USE_PREBUILT_SOLVER AND DEFINED HPIPM_DIR)
    message(STATUS "Using pre-built HPIPM from: ${HPIPM_DIR}")
    set(HPIPM_INCLUDE_DIRS "${HPIPM_DIR}/include")
    set(HPIPM_LIBRARIES "${HPIPM_DIR}/lib/libhpipm.so")
else()
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(HPIPM hpipm)
    endif()
    
    if(NOT HPIPM_FOUND)
        message(STATUS "HPIPM not found. Using C API stubs only")
        set(HPIPM_INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/hpipm_stubs")
        set(HPIPM_LIBRARIES "")
    endif()
endif()

# Eigen
find_package(Eigen3 3.3 QUIET CONFIG)
if(NOT Eigen3_FOUND)
    message(STATUS "System Eigen3 not found, using bundled eigen-5.0.0")
    set(EIGEN3_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/eigen-5.0.0")
endif()

################################################################################
# Include Directories
################################################################################

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${BLASFEO_INCLUDE_DIRS}
    ${HPIPM_INCLUDE_DIRS}
    ${EIGEN3_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/Interfaces
    ${CMAKE_CURRENT_SOURCE_DIR}/hpipm_stubs
)

################################################################################
# Solver Interface Library
################################################################################

add_library(mpc_solver_interface SHARED
    Interfaces/solver_interface.cpp
    Interfaces/hpipm_interface.cpp
)

target_include_directories(mpc_solver_interface PUBLIC
    INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/Interfaces
)

# Only link HPIPM if available
if(HPIPM_LIBRARIES)
    target_link_libraries(mpc_solver_interface PUBLIC
        ${BLASFEO_LIBRARIES}
        ${HPIPM_LIBRARIES}
    )
else()
    target_link_libraries(mpc_solver_interface PUBLIC
        ${BLASFEO_LIBRARIES}
    )
endif()

target_compile_options(mpc_solver_interface PRIVATE
    -Wall -Wextra -Wpedantic
    -O3 -march=native
)

################################################################################
# MPC Solver Library
################################################################################

set(MPC_SOLVER_SOURCES
    types.cpp
    main.cpp
)

if(MPC_SOLVER_SOURCES)
    add_library(mpc_solver SHARED
        ${MPC_SOLVER_SOURCES}
    )

    target_link_libraries(mpc_solver PUBLIC
        mpc_solver_interface
        ${BLASFEO_LIBRARIES}
        ${HPIPM_LIBRARIES}
    )
    
    target_compile_options(mpc_solver PRIVATE
        -Wall -Wextra -Wpedantic
        -O3 -march=native
    )
else()
    message(STATUS "No MPC solver sources specified, skipping mpc_solver library")
endif()

################################################################################
# Installation
################################################################################

if(TARGET mpc_solver)
    install(TARGETS mpc_solver_interface mpc_solver
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin
    )
else()
    install(TARGETS mpc_solver_interface
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin
    )
endif()

install(DIRECTORY Interfaces/
    DESTINATION include/mpc_solver
    FILES_MATCHING PATTERN "*.h"
)

################################################################################
# Print Configuration Summary
################################################################################

message("")
message("===============================================")
message("MPC Controller Configuration Summary")
message("===============================================")
message("")
message("Build type: ${CMAKE_BUILD_TYPE}")
message("C++ standard: ${CMAKE_CXX_STANDARD}")
message("")
message("Dependencies:")
message("  BLASFEO:")
message("    Include: ${BLASFEO_INCLUDE_DIRS}")
message("    Library: ${BLASFEO_LIBRARIES}")
message("  HPIPM:")
message("    Include: ${HPIPM_INCLUDE_DIRS}")
message("    Library: ${HPIPM_LIBRARIES}")
message("  Eigen: ${EIGEN3_INCLUDE_DIR}")
message("")
message("Use pre-built solver: ${USE_PREBUILT_SOLVER}")
message("")
message("Build targets:")
message("  - mpc_solver_interface (Solver abstraction layer)")
message("  - mpc_solver (Main solver library)")
message("")
message("===============================================")
