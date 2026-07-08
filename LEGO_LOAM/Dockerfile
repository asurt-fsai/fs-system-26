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

# Build tooling + LeGO-LOAM's universally-documented native deps (PCL dev
# headers, Eigen3, Boost). NOTE: this base image's userspace is Ubuntu 20.04
# (focal), not jammy -- Humble's official apt repo has no focal-arm64 .debs
# at all, so anything under ros-humble-* below would be a dead end via apt;
# CycloneDDS and GTSAM are both built from source instead.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git vim curl wget unzip \
    cmake build-essential \
    libssl-dev \
    libeigen3-dev \
    libpcl-dev \
    libboost-all-dev \
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

# GTSAM, built from source. Every ROS2 port of LeGO-LOAM documents this same
# requirement -- GTSAM isn't reliably available via apt on focal-arm64, and
# LeGO-LOAM needs a specific version (alpha2 line is what upstream forks
# consistently use; newer GTSAM has had API breaks against LeGO-LOAM code).
# This step is slow -- GTSAM is a large C++ template-heavy library, expect
# this to take a meaningful chunk of the total build time on Xavier's cores.
RUN wget -O /tmp/gtsam.zip https://github.com/borglab/gtsam/archive/4.0.0-alpha2.zip \
    && unzip /tmp/gtsam.zip -d /tmp/ \
    && cd /tmp/gtsam-4.0.0-alpha2 \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && rm -rf /tmp/gtsam.zip /tmp/gtsam-4.0.0-alpha2

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
COPY src/LeGO-LOAM src/LeGO-LOAM/
COPY asurt_msgs asurt_msgs
COPY cloud_msgs cloud_msgs

# Source both the base ROS install AND the CycloneDDS overlay built above,
# so LeGO-LOAM builds against the same workspace and the final
# install/setup.bash exposes everything together.
# NOTE: --packages-select uses the package's NAME from its package.xml /
# CMakeLists.txt project(), which is very likely NOT "LeGO-LOAM" itself
# (ROS2 package names can't contain hyphens). Check the actual name first
# -- e.g. `grep -A1 "<name>" src/LeGO-LOAM/package.xml` -- and swap it in
# below, or just remove --packages-select entirely to build everything
# under src/. Note that cyclonedds and rmw_cyclonedds_cpp also still live
# under /ros2_ws/src from the step above -- a plain `colcon build` here will
# see them again and either skip them (already built, most likely) or
# rebuild them harmlessly; this isn't a bug, just slightly wasteful if it
# re-checks them. Switch to --packages-select once you know the real name
# to avoid that.
RUN rosdep install --from-paths src/LeGO-LOAM --ignore-src -r -y || true \
    && /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && \
       source /ros2_ws/install/setup.bash && \
       colcon build"

# Convenience only -- no ENTRYPOINT script. Appends sourcing to root's
# .bashrc so interactive shells (docker run/exec ... bash) pick up ROS +
# the LeGO-LOAM overlay automatically. Non-interactive commands
# (docker run image <cmd>) won't trigger .bashrc and still need manual
# sourcing, since that's a bash-interactive-shell-only mechanism.
RUN printf '\n# --- ROS2 / LeGO-LOAM auto-source ---\n' >> /root/.bashrc \
    && echo 'if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi' >> /root/.bashrc \
    && echo 'source /ros2_ws/install/setup.bash' >> /root/.bashrc

CMD ["bash"]
