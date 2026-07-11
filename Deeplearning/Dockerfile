# L4T 35.x line = JetPack 5.1.x, matches the Xavier host (L4T 35.6.4).
# "desktop" variant ships rviz2 + the rqt toolset prebuilt.
FROM dustynv/ros:humble-desktop-l4t-r35.4.1
ENV DEBIAN_FRONTEND=noninteractive

# The base image ships a ROS2 apt repo entry (/etc/apt/sources.list.d/) whose
# signing key has since expired (EXPKEYSIG F42ED6FBAB17C654). This breaks
# apt-get update for ALL packages, not just ROS ones, because apt refuses to
# trust any index once one repo's signature fails to verify. Nothing in this
# Dockerfile needs that repo -- CycloneDDS is built from source below, not
# installed via apt -- so the simplest, most reliable fix is to just remove
# the broken repo file before the first apt-get update runs.
RUN rm -f /etc/apt/sources.list.d/ros2*.list /etc/apt/sources.list.d/*ros*.list

# Build tooling only. NOTE: this base image's userspace is Ubuntu 20.04
# (focal), not jammy -- Humble's official apt repo has no focal-arm64 .debs
# at all, so anything under ros-humble-* below would be a dead end via apt.
# CycloneDDS is built from source instead.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git vim curl wget \
    cmake build-essential \
    libssl-dev \
    libopenblas-dev \
    libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep update || true

# Build CycloneDDS (core C library) and rmw_cyclonedds_cpp (the ROS2 RMW
# layer on top of it) from source into the same colcon workspace. Required
# because Humble's apt repo has no arm64 .debs for focal.
#
# Known build issue: cyclonedds's own idlc tool fails with "undefined
# symbol: DDS_XTypes_TypeObject_desc" while generating sources for the
# bundled ddsperf benchmarking CLI -- idlc can't resolve symbols from the
# ddsc shared library it just linked against, because that lib's directory
# isn't on LD_LIBRARY_PATH yet during the build. -DBUILD_DDSPERF=OFF skips
# that optional tool entirely and removes the failure point. LD_LIBRARY_PATH
# is also set as a belt-and-suspenders fix per the upstream maintainer.
RUN mkdir -p /ros2_ws/src \
    && git clone --branch releases/0.10.x --depth 1 \
       https://github.com/eclipse-cyclonedds/cyclonedds.git /ros2_ws/src/cyclonedds \
    && git clone --branch humble --depth 1 \
       https://github.com/ros2/rmw_cyclonedds.git /ros2_ws/src/rmw_cyclonedds \
    && /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && \
       cd /ros2_ws && export LD_LIBRARY_PATH=/opt/ros/humble/lib:\$LD_LIBRARY_PATH && \
       colcon build --packages-up-to rmw_cyclonedds_cpp --cmake-args -DBUILD_DDSPERF=OFF"

# PyTorch for Jetson: regular `pip install torch` does NOT work here --
# PyPI wheels are built for x86_64, not Jetson's ARM64+CUDA/cuDNN stack.
# NVIDIA publishes JetPack-version-specific wheels instead. libopenblas-dev
# and libopenmpi-dev (installed above) are required prerequisites per
# NVIDIA's own install docs and multiple independent guides -- without
# them the wheel can still install via pip but fail or crash on import.
#
# NOTE: an earlier URL here (torch-1.13.0+nv22.10) was sourced from a forum
# post and turned out to 404 -- it doesn't exist in NVIDIA's actual current
# index. Verified directly against the live listing at
# https://developer.download.nvidia.com/compute/redist/jp/v51/pytorch/ --
# as of this writing it has exactly three files:
#   torch-1.14.0a0+44dac51c.nv23.01-cp38-cp38-linux_aarch64.whl
#   torch-1.14.0a0+44dac51c.nv23.02-cp38-cp38-linux_aarch64.whl
#   torch-2.0.0a0+8aa34602.nv23.03-cp38-cp38-linux_aarch64.whl
# Using the newest (2.0.0a0) below. If planning_deep_learning's code relies
# on an older torch API or breaks against 2.0, swap this URL for one of the
# 1.14.0a0 ones instead -- check the live index above for the current file
# list, since NVIDIA does add/remove files from this directory over time.
RUN pip3 install --no-cache-dir --ignore-installed \
    https://developer.download.nvidia.com/compute/redist/jp/v51/pytorch/torch-2.0.0a0+8aa34602.nv23.03-cp38-cp38-linux_aarch64.whl

# Known issue across multiple independent Jetson/PyTorch guides: numpy +
# OpenBLAS on ARM can crash with "Illegal instruction (core dumped)" at
# import time without this env var. Cheap, harmless safety net.
ENV OPENBLAS_CORETYPE=ARMV8

# Confirm rviz2 + rqt_graph are present (the desktop variant ships them
# prebuilt -- this just fails the build loudly if that's ever not true,
# instead of finding out at runtime).
RUN /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && which rviz2 && which rqt_graph"

# RMW / DDS config. ROS_LOCALHOST_ONLY=0 + `docker run --network host` lets
# you discover peers across machines. Replace placeholder IPs before
# building, OR override CYCLONEDDS_URI at `docker run -e ...` time instead
# if peer IPs change often (avoids rebuilding the image per IP change).
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_LOCALHOST_ONLY=0
ENV CYCLONEDDS_URI="<CycloneDDS><Domain><General><Interfaces><NetworkInterface autodetermine=\"true\" /></Interfaces></General><Discovery><Peers><Peer address=\"LAPTOP1_IP_HERE\"/><Peer address=\"LAPTOP2_IP_HERE\"/></Peers><ParticipantIndex>auto</ParticipantIndex></Discovery></Domain></CycloneDDS>"

WORKDIR /ros2_ws
# Source layout confirmed: src/planning_node/planning_deep_learning/ is the
# actual ament_python package root (has package.xml, setup.py, setup.cfg).
COPY src/planning_deep_learning src/planning_deep_learning/

# NOTE: entry point / console_script name inside setup.py was not confirmed
# before writing this Dockerfile -- this is a known unknown, intentionally
# left for the trial-and-error pass requested. `colcon build` here builds
# whatever's under src/ (planning_deep_learning + the already-built
# cyclonedds/rmw_cyclonedds_cpp, which colcon should skip as already done).
# rosdep install is included in case package.xml declares any ROS-mapped
# deps; it won't catch plain pip imports inside model.py/node.py -- those
# get caught and added once you hit ModuleNotFoundError errors at launch,
# same pattern used for lidarpipeline's open3d/pandas.
RUN rosdep install --from-paths src/planning_deep_learning --ignore-src -r -y || true \
    && /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && \
       source /ros2_ws/install/setup.bash && \
       colcon build"

# Convenience only -- no ENTRYPOINT script. Appends sourcing to root's
# .bashrc so interactive shells (docker run/exec ... bash) pick up ROS +
# the planning_deep_learning overlay automatically. Non-interactive
# commands (docker run image <cmd>) won't trigger .bashrc and still need
# manual sourcing, since that's a bash-interactive-shell-only mechanism.
RUN printf '\n# --- ROS2 / planning_deep_learning auto-source ---\n' >> /root/.bashrc \
    && echo 'if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi' >> /root/.bashrc \
    && echo 'source /ros2_ws/install/setup.bash' >> /root/.bashrc

CMD ["bash"]
