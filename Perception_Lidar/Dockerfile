# L4T 35.x line = JetPack 5.1.x, matches the Xavier host (L4T 35.6.4).
# "desktop" variant ships rviz2 + the rqt toolset prebuilt.
FROM dustynv/ros:humble-desktop-l4t-r35.4.1
ENV DEBIAN_FRONTEND=noninteractive

# The base image ships a ROS2 apt repo entry (/etc/apt/sources.list.d/) whose
# signing key has since expired (EXPKEYSIG F42ED6FBAB17C654). This breaks
# apt-get update for ALL packages, not just ROS ones, because apt refuses to
# trust any index once one repo's signature fails to verify. Nothing in this
# Dockerfile actually needs that repo -- CycloneDDS is built from source
# below, not installed via apt -- so the simplest, most reliable fix is to
# just remove the broken repo file before the first apt-get update runs.
RUN rm -f /etc/apt/sources.list.d/ros2*.list /etc/apt/sources.list.d/*ros*.list

# Build tooling only. NOTE: this base image's userspace is Ubuntu 20.04
# (focal), not jammy -- confirmed via lsb_release inside the container.
# Humble's official apt repo only ships rmw_cyclonedds_cpp .debs for focal on
# amd64, not arm64/Jetson -- so apt-get install ros-humble-rmw-cyclonedds-cpp
# would be a dead end on this image even with a working repo. CycloneDDS +
# its RMW layer are built from source below instead, which is the standard
# fix for Humble-on-Focal-arm64 images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    git vim curl \
    cmake build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies for lidarpipeline (lidar_processor_node.py, Filter.py,
# EuclideanClustering.py, ConeClassifier.py, LUTBoundingBoxFilter.py).
# rosdep doesn't catch these since they're plain pip imports, not
# ROS/rosdep-mapped packages.
# NOTE: pip-installed open3d has NO CUDA support on ARM64/Jetson (CPU-only
# point cloud ops). If any node relies on GPU-accelerated open3d calls,
# you'd need to build open3d from source with -DBUILD_CUDA_MODULE=ON
# instead -- see https://www.open3d.org/docs/release/arm.html
#
# --ignore-installed is required here: open3d pulls in dash/flask, which
# wants a newer 'blinker' than the one baked into this image's base Python
# via distutils (apt-installed, not pip-installed). pip refuses to
# uninstall distutils-owned packages since it can't safely determine which
# files belong to them -- --ignore-installed tells pip to install the new
# version alongside it instead of attempting that uninstall.
#
# numpy is pinned explicitly even though it likely rides in transitively
# via open3d, so a future open3d version bump can't silently drop it.
RUN pip3 install --no-cache-dir --ignore-installed open3d numpy pandas

RUN rosdep update || true

# Build CycloneDDS (core C library) and rmw_cyclonedds_cpp (the ROS2 RMW
# layer on top of it) from source into the same colcon workspace. Cloning
# the 'humble' / 'iron' branch on cyclonedds (release line) keeps it aligned
# with Humble's rmw_cyclonedds_cpp expectations.
#
# Known build issue: cyclonedds's own idlc tool fails with
# "undefined symbol: DDS_XTypes_TypeObject_desc" while generating sources for
# the bundled ddsperf benchmarking CLI -- idlc can't resolve symbols from the
# ddsc shared library it just linked against, because that lib's directory
# isn't on LD_LIBRARY_PATH yet during the build. ddsperf is an optional
# performance-testing tool we don't need, so -DBUILD_DDSPERF=OFF skips it
# entirely and removes the failure point. --cmake-args is harmlessly ignored
# by rmw_cyclonedds_cpp, which doesn't define that option. LD_LIBRARY_PATH is
# also set as a belt-and-suspenders fix per the upstream maintainer's advice.
RUN mkdir -p /ros2_ws/src \
    && git clone --branch releases/0.10.x --depth 1 \
       https://github.com/eclipse-cyclonedds/cyclonedds.git /ros2_ws/src/cyclonedds \
    && git clone --branch humble --depth 1 \
       https://github.com/ros2/rmw_cyclonedds.git /ros2_ws/src/rmw_cyclonedds \
    && /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && \
       cd /ros2_ws && export LD_LIBRARY_PATH=/opt/ros/humble/lib:\$LD_LIBRARY_PATH && \
       colcon build --packages-up-to rmw_cyclonedds_cpp --cmake-args -DBUILD_DDSPERF=OFF"

# Confirm rviz2 + rqt_graph are present (the desktop variant ships them
# prebuilt -- this just fails the build loudly if that's ever not true,
# instead of finding out at runtime).
RUN /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && which rviz2 && which rqt_graph"

# RMW / DDS config. ROS_LOCALHOST_ONLY=0 + network_mode host lets you discover
# peers across machines. Replace the placeholder IPs with your real laptop
# addresses before building, OR override CYCLONEDDS_URI at `docker run -e ...`
# time if peer IPs change often (avoids rebuilding the image).
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_LOCALHOST_ONLY=0
ENV CYCLONEDDS_URI="<CycloneDDS><Domain><General><Interfaces><NetworkInterface autodetermine=\"true\" /></Interfaces></General><Discovery><Peers><Peer address=\"LAPTOP1_IP_HERE\"/><Peer address=\"LAPTOP2_IP_HERE\"/></Peers><ParticipantIndex>auto</ParticipantIndex></Discovery></Domain></CycloneDDS>"

WORKDIR /ros2_ws
COPY src/lidarpipeline src/lidarpipeline/

# Source both the base ROS install AND the CycloneDDS overlay built above,
# so lidarpipeline builds against the same workspace and the final
# install/setup.bash exposes everything together.
RUN rosdep install --from-paths src/lidarpipeline --ignore-src -r -y || true \
    && /bin/bash -c "if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi && \
       source /ros2_ws/install/setup.bash && \
       colcon build --packages-select lidarpipeline"

# Convenience only -- no ENTRYPOINT script per request. Appends sourcing to
# root's .bashrc so interactive shells (docker run/exec ... bash) pick up
# ROS + the lidarpipeline overlay automatically. Non-interactive commands
# (docker run image <cmd>) won't trigger .bashrc and still need manual
# sourcing, since that's a bash-interactive-shell-only mechanism.
RUN printf '\n# --- ROS2 / lidarpipeline auto-source ---\n' >> /root/.bashrc \
    && echo 'if [ -f /opt/ros/humble/install/setup.bash ]; then source /opt/ros/humble/install/setup.bash; else source /opt/ros/humble/setup.bash; fi' >> /root/.bashrc \
    && echo 'source /ros2_ws/install/setup.bash' >> /root/.bashrc

CMD ["bash"]
