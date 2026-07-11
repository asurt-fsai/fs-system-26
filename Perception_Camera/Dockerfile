# syntax=docker/dockerfile:1
#
# ZED camera package. Base is Stereolabs' own SDK image (pure Ubuntu 20.04
# focal / L4T r35.4, zero ROS2 inside). ROS2 Humble + CycloneDDS are built
# from source on top of it here.
#
# Why from source, not apt: packages.ros.org never published Humble debs for
# arm64-focal (only amd64-focal / arm64-jammy) -- the entire reason this
# image is on Focal in the first place. The one apt mirror that ever did
# publish focal-arm64 Humble binaries was NVIDIA's Isaac ROS Buildfarm, but
# per NVIDIA's own docs that buildfarm was PERMANENTLY discontinued on
# 2025-06-30 ("an isolated infrastructure event... no longer available").
# That's not an outage to retry around -- there is no apt path left on this
# OS/arch combination, so this build compiles ROS2 itself.
#
# L4T tag pinned to r35.4 to match the r35.4.1 family used by the
# lidarpipeline / simple_pure_pursuit images (host is L4T 35.6.4, same major
# release). ZED SDK 4.0 assumed to match that same generation -- bump the
# tag below if a different SDK version is actually installed on the Xavier.
FROM stereolabs/zed:4.0-devel-l4t-r35.4

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV LANG=en_US.UTF-8

# --- Locale + base tooling ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
        curl \
        gnupg2 \
        ca-certificates \
        lsb-release \
        software-properties-common \
        build-essential \
        cmake \
        git \
        wget \
        python3-pip \
        python3-dev \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# --- ROS2 build tooling via pip ---
# No apt repo on this platform carries colcon/vcstool/rosdep either (same
# arm64-focal gap as above), so these come from pip rather than
# ros-dev-tools. Plain `pip3 install`, no --break-system-packages -- that
# flag only applies to PEP 668-enforcing Ubuntu 23.04+, not this Focal base.
# catkin_pkg and rosdistro are included here too: their Debian-wrapped forms
# (python3-catkin-pkg-modules, python3-rosdistro-modules) are distributed via
# the ROS apt repo specifically, not plain Ubuntu universe, so they hit the
# same arm64-focal gap -- skipped via --skip-keys below and satisfied by
# these pip installs instead (same import names either way).
RUN pip3 install -U \
        colcon-common-extensions \
        vcstool \
        rosdep \
        rosinstall-generator \
        catkin_pkg \
        rosdistro \
    && rosdep init || true

# --- Universe repo + remaining build dependencies ---
# These are plain Ubuntu/Focal packages (not ROS-distro-specific), so the
# normal Ubuntu mirrors already in the image cover them -- no extra apt
# source needed for this step.
RUN add-apt-repository universe \
    && apt-get update && apt-get install -y --no-install-recommends \
        libpython3-dev \
        python3-flake8-docstrings \
        python3-pytest-cov \
        libacl1-dev \
        libasio-dev \
        libtinyxml2-dev \
        libcunit1-dev \
        liblog4cxx-dev \
    && rm -rf /var/lib/apt/lists/*

# --- ROS2 Humble + CycloneDDS RMW: fetched and built from source ---
# rosinstall_generator scopes the checkout to just ros_base + the CycloneDDS
# RMW and their transitive deps (cyclonedds + rmw_cyclonedds_cpp come along
# automatically as dependencies of rmw_cyclonedds_cpp) -- this avoids
# cloning + building the full desktop variant (rviz, demos, etc.), which
# would roughly double build time for nothing this stack needs.
WORKDIR /opt/ros/humble
RUN rosinstall_generator --deps --rosdistro humble \
        ros_base rmw_cyclonedds_cpp launch_testing_ament_cmake \
        > /tmp/ros2_humble.repos \
    && mkdir -p src \
    && vcs import --input /tmp/ros2_humble.repos src

# apt-get update is required here: the previous layer's `rm -rf
# /var/lib/apt/lists/*` wiped the package index, and rosdep's apt installer
# does NOT refresh it itself -- without this, every single apt-get install
# rosdep attempts fails with "unable to locate package," even for completely
# ordinary packages like libeigen3-dev.
RUN apt-get update \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y \
        --rosdistro humble \
        --skip-keys "fastcdr rti-connext-dds-5.3.1 rti-connext-dds-6.0.1 urdfdom_headers python3-catkin-pkg-modules python3-rosdistro-modules" \
    && rm -rf /var/lib/apt/lists/*

# -DBUILD_DDSPERF=OFF is the same fix already proven on lidarpipeline /
# simple_pure_pursuit: works around idlc's undefined-symbol crash in the
# optional ddsperf benchmarking tool (upstream eclipse-cyclonedds#2034).
# Applying it as a global --cmake-args is harmless to every other package in
# this build -- CMake just ignores the unused variable for anything that
# isn't cyclonedds itself.
RUN colcon build \
        --merge-install \
        --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_DDSPERF=OFF

ENV LD_LIBRARY_PATH=/opt/ros/humble/install/lib:${LD_LIBRARY_PATH}

# --- Workspace: copy in project sources ---
# "src" lands directly as the workspace's src/ contents; asurt_msgs and
# tf_helper are separate ROS packages copied in as siblings, matching the
# layout used for simple_pure_pursuit.
#
# NOTE on rosdep here: since ROS2 itself isn't apt-installed in this image,
# rosdep can't resolve "already satisfied by ros-humble-*" the normal way.
# This call will still catch genuine non-ROS system libraries, but if
# asurt_msgs / tf_helper / src depend on anything beyond core ROS2 client
# libraries (already present from the build above) or pip-importable
# packages, add explicit apt/pip install lines here -- same pattern as the
# open3d/pandas fix on lidarpipeline.
WORKDIR /opt/ros_ws
COPY src/ ./src/
COPY asurt_msgs/ ./src/asurt_msgs/
COPY tf_helper/ ./src/tf_helper/
COPY run_tests.sh ./run_tests.sh
RUN chmod +x ./run_tests.sh

RUN /bin/bash -c "source /opt/ros/humble/install/setup.bash \
        && apt-get update \
        && rosdep install --from-paths src --ignore-src -r -y || true \
        && rm -rf /var/lib/apt/lists/* \
        && colcon build --merge-install --symlink-install"

# --- Auto-source on every interactive shell ---
# Defensively checks both the merge-install and non-merge-install setup.bash
# locations, same as lidarpipeline / simple_pure_pursuit -- this build uses
# --merge-install, so /opt/ros/humble/install/setup.bash is the one that
# will actually exist, but the fallback costs nothing. No entrypoint script
# -- this only fires for interactive bash sessions, not
# `docker run image <cmd>`.
RUN { \
        echo ''; \
        echo '# --- auto-source ROS2 + workspace overlay ---'; \
        echo 'if [ -f /opt/ros/humble/install/setup.bash ]; then'; \
        echo '    source /opt/ros/humble/install/setup.bash'; \
        echo 'elif [ -f /opt/ros/humble/setup.bash ]; then'; \
        echo '    source /opt/ros/humble/setup.bash'; \
        echo 'fi'; \
        echo 'if [ -f /opt/ros_ws/install/setup.bash ]; then'; \
        echo '    source /opt/ros_ws/install/setup.bash'; \
        echo 'fi'; \
    } >> /root/.bashrc

WORKDIR /opt/ros_ws
