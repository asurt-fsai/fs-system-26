FROM dustynv/ros:humble-ros-base-l4t-r35.4.1

ENV DEBIAN_FRONTEND=noninteractive

# Fix expired GPG key
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu focal main" \
        > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-matplotlib \
    python3-pcl \
    liblapack-dev \
    libblas-dev \
    gfortran \
    vim \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep update || true

# Small packages first
RUN pip install --timeout=1000 \
    "numpy>=1.22,<2.0" \
    scipy \
    transforms3d \
    icecream \
    typing_extensions \
    transformations \
    --upgrade

# llvmlite and numba separately — large files need more time
RUN pip install --timeout=1000 llvmlite
RUN pip install --timeout=1000 numba

RUN pip install --timeout=1000 git+https://github.com/DLu/tf_transformations.git

WORKDIR /ros2_ws

COPY src/planning_centerline_calc_MIX_FINALFINALFINAL \
     src/planning_centerline_calc_MIX_FINALFINALFINAL/
COPY src/asurt_msgs src/asurt_msgs/
COPY src/tf_helper src/tf_helper/

# Fix Python 3.8 incompatibility with new-style type hints
RUN find /ros2_ws/src -name "*.py" | while read f; do \
        grep -q "from __future__ import annotations" "$f" \
        || sed -i '1s/^/from __future__ import annotations\n/' "$f"; \
    done

RUN ROS_SETUP=$(find /opt /usr -name "setup.bash" 2>/dev/null | grep ros | head -1) \
    && /bin/bash -c "source $ROS_SETUP && colcon build"

RUN ROS_SETUP=$(find /opt /usr -name "setup.bash" 2>/dev/null | grep ros | head -1) \
    && echo "source $ROS_SETUP" >> /root/.bashrc \
    && echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

CMD ["/bin/bash"]
