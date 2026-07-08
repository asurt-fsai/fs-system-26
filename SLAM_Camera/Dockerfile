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
    vim \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep update || true

WORKDIR /ros2_ws

COPY src/cone_mapping src/cone_mapping/


RUN ROS_SETUP=$(find /opt /usr -name "setup.bash" 2>/dev/null | grep ros | head -1) \
    && /bin/bash -c "source $ROS_SETUP && colcon build"

RUN ROS_SETUP=$(find /opt /usr -name "setup.bash" 2>/dev/null | grep ros | head -1) \
    && echo "source $ROS_SETUP" >> /root/.bashrc \
    && echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

CMD ["/bin/bash"]
