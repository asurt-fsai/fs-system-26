FROM dustynv/ros:humble-ros-base-l4t-r35.4.1
ENV DEBIAN_FRONTEND=noninteractive

# The base image ships a ROS2 apt repo entry (/etc/apt/sources.list.d/)
# whose signing key has expired (EXPKEYSIG F42ED6FBAB17C654). This breaks
# apt-get update for ALL packages, not just ROS ones, because apt refuses
# to trust any index once one repo's signature fails to verify. Separately
# confirmed that even a valid key wouldn't help here: packages.ros.org's
# focal repo only ships Humble .debs for amd64, not arm64/Jetson, so this
# repo can never provide anything usable on this image regardless. Nothing
# below needs it (CycloneDDS is built from source), so removing the file
# is the simplest, most reliable fix.
RUN rm -f /etc/apt/sources.list.d/ros2*.list /etc/apt/sources.list.d/*ros*.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pcl \
    cmake build-essential \
    libssl-dev \
    vim \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep update || true

RUN pip3 install --no-cache-dir --ignore-installed transformations --upgrade

# This base image uses ROS's --merge-install layout, so setup.bash lives at
# /opt/ros/<distro>/install/setup.bash, not /opt/ros/<distro>/setup.bash.
# A bare `find | grep ros | head -1` is fragile -- it can match unrelated
# files anywhere under /opt or /usr and silently pick the wrong one. This
# script checks the two known-correct locations explicitly instead, and
# fails loudly if neither exists, rather than silently sourcing garbage.
# (Using printf instead of a RUN heredoc -- heredocs in RUN need newer
# BuildKit Dockerfile syntax that may not be available/tested on this setup.)
RUN printf '#!/bin/bash\nset -e\nif [ -f "/opt/ros/${ROS_DISTRO}/install/setup.bash" ]; then\n    echo "/opt/ros/${ROS_DISTRO}/install/setup.bash"\nelif [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then\n    echo "/opt/ros/${ROS_DISTRO}/setup.bash"\nelse\n    echo "ERROR: no ROS setup.bash found" >&2\n    exit 1\nfi\n' > /usr/local/bin/find_ros_setup.sh \
    && chmod +x /usr/local/bin/find_ros_setup.sh

# Build CycloneDDS (core C library) and rmw_cyclonedds_cpp from source.
# Required because Humble's official apt repo has no arm64 .debs for focal
# (this image's userspace), so apt-get install ros-humble-rmw-cyclonedds-cpp
# is not an option here regardless of the apt-key situation above.
#
# Known build issue: cyclonedds's idlc tool can throw "undefined symbol:
# DDS_XTypes_TypeObject_desc" while generating sources for the optional
# ddsperf benchmarking CLI, because the freshly-built ddsc shared library
# isn't yet on LD_LIBRARY_PATH during the build. -DBUILD_DDSPERF=OFF skips
# that tool entirely (not needed for the RMW to function) and removes the
# failure point; LD_LIBRARY_PATH is set too as a belt-and-suspenders fix.
RUN ROS_SETUP=$(/usr/local/bin/find_ros_setup.sh) \
    && mkdir -p /opt/deps_ws/src \
    && git clone --branch releases/0.10.x --depth 1 \
       https://github.com/eclipse-cyclonedds/cyclonedds.git /opt/deps_ws/src/cyclonedds \
    && git clone --branch humble --depth 1 \
       https://github.com/ros2/rmw_cyclonedds.git /opt/deps_ws/src/rmw_cyclonedds \
    && /bin/bash -c "source $ROS_SETUP && \
       cd /opt/deps_ws && export LD_LIBRARY_PATH=/opt/ros/\$ROS_DISTRO/lib:\$LD_LIBRARY_PATH && \
       colcon build --packages-up-to rmw_cyclonedds_cpp --cmake-args -DBUILD_DDSPERF=OFF"

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_LOCALHOST_ONLY=0

# Find ROS setup.bash and build ackermann_msgs from source, into the SAME
# /opt/deps_ws used above for CycloneDDS, so both end up under one
# install/setup.bash instead of two separate overlays.
RUN ROS_SETUP=$(/usr/local/bin/find_ros_setup.sh) \
    && cd /opt/deps_ws/src \
    && git clone https://github.com/ros-drivers/ackermann_msgs.git -b ros2 \
    && cd /opt/deps_ws \
    && /bin/bash -c "source $ROS_SETUP && colcon build"

WORKDIR /ros2_ws
COPY src/simple_pure_pursuit src/simple_pure_pursuit/
COPY src/asurt_msgs src/asurt_msgs/
COPY src/tf_helper src/tf_helper/

RUN ROS_SETUP=$(/usr/local/bin/find_ros_setup.sh) \
    && /bin/bash -c "source $ROS_SETUP \
    && source /opt/deps_ws/install/setup.bash \
    && cd /ros2_ws \
    && colcon build"

# Auto-source on interactive shells (no ENTRYPOINT script). Appends to
# root's .bashrc so `docker run/exec -it ... bash` gets ROS + the
# CycloneDDS/ackermann_msgs overlay + this workspace automatically.
# Non-interactive `docker run image <cmd>` won't trigger .bashrc and still
# needs manual sourcing, since that's a bash-interactive-only mechanism.
RUN ROS_SETUP=$(/usr/local/bin/find_ros_setup.sh) \
    && printf '\n# --- ROS2 auto-source ---\n' >> /root/.bashrc \
    && echo "source $ROS_SETUP" >> /root/.bashrc \
    && echo 'source /opt/deps_ws/install/setup.bash' >> /root/.bashrc \
    && echo 'source /ros2_ws/install/setup.bash' >> /root/.bashrc

CMD ["/bin/bash"]
