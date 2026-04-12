################################################################################
# CMakeLists.txt — MPC Solver with BLASFEO / HPIPM
#
# Build strategy (priority order):
#   1. If build_solver.sh has already installed libraries → use install/
#   2. Otherwise build BLASFEO from embedded source (blasfeo/)
#   3. If HPIPM library present → build hpipm-cpp-main C++ wrapper too
#   4. Without HPIPM → compile with stub headers only (no actual QP solve)
#
# Usage:
#   mkdir build && cd build
#   cmake ..        # auto-detects what is available
#   make -j$(nproc)
################################################################################

cmake_minimum_required(VERSION 3.10)

project(MPCController
    VERSION 1.0.0
    DESCRIPTION "Model Predictive Control with HPIPM Solver"
    LANGUAGES CXX C
)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

################################################################################
# Locate Eigen
################################################################################

find_package(Eigen3 3.3 QUIET CONFIG)
if(NOT Eigen3_FOUND)
    message(STATUS "System Eigen3 not found — using bundled eigen-5.0.0")
    set(EIGEN3_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/eigen-5.0.0")
    add_library(Eigen3::Eigen INTERFACE IMPORTED)
    target_include_directories(Eigen3::Eigen INTERFACE ${EIGEN3_INCLUDE_DIR})
endif()

################################################################################
# Locate nlohmann/json (needed by Params)
################################################################################

# Package-level include directory (mpc_controller/include/)
set(NLOHMANN_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../include")
if(NOT EXISTS "${NLOHMANN_INCLUDE_DIR}/nlohmann/json.hpp")
    # Try system install
    find_path(NLOHMANN_INCLUDE_DIR nlohmann/json.hpp
        PATHS /usr/include /usr/local/include)
endif()

################################################################################
# BLASFEO
################################################################################

set(BLASFEO_SRC_DIR    "${CMAKE_CURRENT_SOURCE_DIR}/blasfeo")
set(BLASFEO_BUILD_DIR  "${CMAKE_CURRENT_SOURCE_DIR}/build_solver/blasfeo")
set(BLASFEO_INSTALL    "${CMAKE_CURRENT_SOURCE_DIR}/install")

# Option A: already installed by build_solver.sh
if(EXISTS "${BLASFEO_INSTALL}/lib/libblasfeo.so")
    message(STATUS "BLASFEO: using installed library at ${BLASFEO_INSTALL}")
    set(BLASFEO_INCLUDE_DIRS "${BLASFEO_INSTALL}/include")
    set(BLASFEO_LIBRARIES    "${BLASFEO_INSTALL}/lib/libblasfeo.so")

# Option B: built in-source but not installed
elseif(EXISTS "${BLASFEO_BUILD_DIR}/libblasfeo.so")
    message(STATUS "BLASFEO: using pre-built library at ${BLASFEO_BUILD_DIR}")
    set(BLASFEO_INCLUDE_DIRS "${BLASFEO_SRC_DIR}/include")
    set(BLASFEO_LIBRARIES    "${BLASFEO_BUILD_DIR}/libblasfeo.so")

# Option C: build from source now via ExternalProject / add_subdirectory
elseif(EXISTS "${BLASFEO_SRC_DIR}/CMakeLists.txt")
    message(STATUS "BLASFEO: building from source at ${BLASFEO_SRC_DIR}")

    # Detect CPU for BLASFEO target
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64")
        include(CheckCXXCompilerFlag)
        check_cxx_compiler_flag("-mavx512f" COMPILER_SUPPORTS_AVX512)
        check_cxx_compiler_flag("-mavx2"    COMPILER_SUPPORTS_AVX2)
        if(COMPILER_SUPPORTS_AVX512)
            set(BLASFEO_TARGET "X64_INTEL_SKYLAKE_X")
        elseif(COMPILER_SUPPORTS_AVX2)
            set(BLASFEO_TARGET "X64_INTEL_HASWELL")
        else()
            set(BLASFEO_TARGET "GENERIC")
        endif()
    else()
        set(BLASFEO_TARGET "GENERIC")
    endif()
    message(STATUS "BLASFEO target: ${BLASFEO_TARGET}")

    set(BLASFEO_OUT_DIR "${CMAKE_BINARY_DIR}/blasfeo_build")
    add_subdirectory(${BLASFEO_SRC_DIR} blasfeo_build EXCLUDE_FROM_ALL)

    # After add_subdirectory the target 'blasfeo' is available
    set(BLASFEO_INCLUDE_DIRS "${BLASFEO_SRC_DIR}/include")
    set(BLASFEO_LIBRARIES    blasfeo)          # CMake target name

else()
    message(WARNING "BLASFEO not found — solver will be stub only")
    set(BLASFEO_INCLUDE_DIRS "${BLASFEO_SRC_DIR}/include")
    set(BLASFEO_LIBRARIES    "")
endif()

################################################################################
# HPIPM (optional)
################################################################################

# Search in install/ first, then system paths
find_library(HPIPM_LIB hpipm
    HINTS "${BLASFEO_INSTALL}/lib" /usr/local/lib /usr/lib
    NO_DEFAULT_PATH)

if(HPIPM_LIB)
    message(STATUS "HPIPM: found at ${HPIPM_LIB}")

    # Find headers — prefer install/, then system
    find_path(HPIPM_INCLUDE_DIR hpipm_d_ocp_qp_ipm.h
        HINTS "${BLASFEO_INSTALL}/include" /usr/local/include /usr/include
        NO_DEFAULT_PATH)

    if(NOT HPIPM_INCLUDE_DIR)
        set(HPIPM_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/hpipm_stubs")
    endif()
    message(STATUS "HPIPM include: ${HPIPM_INCLUDE_DIR}")

    set(HPIPM_FOUND    TRUE)
    set(HPIPM_LIBRARIES "${HPIPM_LIB}")

    # ── Build hpipm-cpp C++ wrapper directly from source ──────────────────
    # We do NOT use add_subdirectory(hpipm-cpp-main) because its CMakeLists.txt
    # calls find_package(blasfeo/hpipm REQUIRED) which needs installed cmake
    # config files we don't have. Instead, compile the wrapper sources directly.
    set(HPIPM_CPP_SRC "${CMAKE_CURRENT_SOURCE_DIR}/hpipm-cpp-main/src")
    if(EXISTS "${HPIPM_CPP_SRC}/ocp_qp_ipm_solver.cpp")
        add_library(hpipm_cpp_wrapper STATIC
            ${HPIPM_CPP_SRC}/detail/d_ocp_qp_dim_wrapper.cpp
            ${HPIPM_CPP_SRC}/detail/d_ocp_qp_wrapper.cpp
            ${HPIPM_CPP_SRC}/detail/d_ocp_qp_sol_wrapper.cpp
            ${HPIPM_CPP_SRC}/detail/d_ocp_qp_ipm_arg_wrapper.cpp
            ${HPIPM_CPP_SRC}/detail/d_ocp_qp_ipm_ws_wrapper.cpp
            ${HPIPM_CPP_SRC}/ocp_qp_dim.cpp
            ${HPIPM_CPP_SRC}/ocp_qp_ipm_solver_settings.cpp
            ${HPIPM_CPP_SRC}/ocp_qp_ipm_solver_statistics.cpp
            ${HPIPM_CPP_SRC}/ocp_qp_ipm_solver.cpp
        )
        target_include_directories(hpipm_cpp_wrapper PUBLIC
            ${CMAKE_CURRENT_SOURCE_DIR}/hpipm-cpp-main/include
            ${BLASFEO_INCLUDE_DIRS}
            ${HPIPM_INCLUDE_DIR}
            ${EIGEN3_INCLUDE_DIR}
        )
        target_link_libraries(hpipm_cpp_wrapper PUBLIC
            ${BLASFEO_LIBRARIES}
            ${HPIPM_LIBRARIES}
            Eigen3::Eigen
        )
        set_target_properties(hpipm_cpp_wrapper PROPERTIES POSITION_INDEPENDENT_CODE ON)
        set(HPIPM_CPP_AVAILABLE TRUE)
        message(STATUS "hpipm-cpp: C++ wrapper will be built from source")
    else()
        message(STATUS "hpipm-cpp: source not found, wrapper disabled")
    endif()
else()
    message(STATUS "HPIPM not found — using stub headers, solver disabled")
    set(HPIPM_FOUND        FALSE)
    set(HPIPM_LIBRARIES    "")
    set(HPIPM_INCLUDE_DIR  "${CMAKE_CURRENT_SOURCE_DIR}/hpipm_stubs")
endif()

################################################################################
# Global include directories
################################################################################

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${BLASFEO_INCLUDE_DIRS}
    ${HPIPM_INCLUDE_DIR}
    ${EIGEN3_INCLUDE_DIR}
    ${NLOHMANN_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/hpipm_stubs
    ${CMAKE_CURRENT_SOURCE_DIR}/hpipm-cpp-main/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../include   # package-level include/
)

################################################################################
# Solver interface library (hpipm_interface + solver_interface)
################################################################################

add_library(mpc_solver_interface SHARED
    Interfaces/solver_interface.cpp
    Interfaces/hpipm_interface.cpp
)

target_include_directories(mpc_solver_interface PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/Interfaces>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<BUILD_INTERFACE:${BLASFEO_INCLUDE_DIRS}>
    $<BUILD_INTERFACE:${HPIPM_INCLUDE_DIR}>
    $<INSTALL_INTERFACE:include/mpc_solver>
)

target_compile_options(mpc_solver_interface PRIVATE -Wall -Wextra -O3 -march=native)

# Activate hpipm-cpp path when the wrapper is available
if(HPIPM_CPP_AVAILABLE)
    target_compile_definitions(mpc_solver_interface PRIVATE HPIPM_CPP_AVAILABLE)
    target_include_directories(mpc_solver_interface PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/hpipm-cpp-main/include)
    target_link_libraries(mpc_solver_interface PUBLIC
        hpipm_cpp_wrapper           # Compiled from hpipm-cpp-main/src/
        ${BLASFEO_LIBRARIES}
        ${HPIPM_LIBRARIES}
        Eigen3::Eigen
    )
else()
    target_link_libraries(mpc_solver_interface PUBLIC
        ${BLASFEO_LIBRARIES}
        Eigen3::Eigen
    )
endif()

################################################################################
# Full MPC library (all modules)
################################################################################

set(MPC_SOURCES
    types.cpp
    config.cpp
    Params/params.cpp
    "Bicycle Model/bicycle_model.cpp"
    Integrator/integration_methods.cpp
    Cost/cost.cpp
    Constraints/constraints.cpp
    Constraints/trackConstraints.cpp
    Spline/Arc_Spline.cpp
    Spline/Cubic_Spline.cpp
    MPC/mpc.cpp
)

# Check which sources actually exist
set(MPC_SOURCES_EXISTING "")
foreach(src ${MPC_SOURCES})
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${src}")
        list(APPEND MPC_SOURCES_EXISTING "${src}")
    else()
        message(WARNING "MPC source not found (skipped): ${src}")
    endif()
endforeach()

if(MPC_SOURCES_EXISTING)
    add_library(mpc_core SHARED ${MPC_SOURCES_EXISTING})

    target_include_directories(mpc_core PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${EIGEN3_INCLUDE_DIR}>
        $<BUILD_INTERFACE:${NLOHMANN_INCLUDE_DIR}>
    )

    target_link_libraries(mpc_core PUBLIC
        mpc_solver_interface
        Eigen3::Eigen
    )

    target_compile_options(mpc_core PRIVATE -Wall -Wextra -O3 -march=native)
endif()

################################################################################
# Installation
################################################################################

set(INSTALL_TARGETS mpc_solver_interface)
if(TARGET mpc_core)
    list(APPEND INSTALL_TARGETS mpc_core)
endif()

install(TARGETS ${INSTALL_TARGETS}
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY Interfaces/
    DESTINATION include/mpc_solver
    FILES_MATCHING PATTERN "*.h"
)

################################################################################
# Summary
################################################################################

message("")
message("======================================================")
message("MPC Controller Build Configuration")
message("======================================================")
message("  BLASFEO include : ${BLASFEO_INCLUDE_DIRS}")
message("  BLASFEO lib     : ${BLASFEO_LIBRARIES}")
message("  HPIPM found     : ${HPIPM_FOUND}")
if(HPIPM_FOUND)
message("  HPIPM lib       : ${HPIPM_LIBRARIES}")
message("  hpipm-cpp       : ${HPIPM_CPP_AVAILABLE}")
endif()
message("  Eigen           : ${EIGEN3_INCLUDE_DIR}")
message("  nlohmann/json   : ${NLOHMANN_INCLUDE_DIR}")
message("======================================================")
message("")
