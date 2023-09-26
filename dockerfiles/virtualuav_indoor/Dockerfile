FROM lmark1/uav_ros_stack:focal

# Use ARG - persists only during docker build
# https://github.com/moby/moby/issues/4032#issuecomment-192327844
ARG CATKIN_WORKSPACE=uav_ws
ARG ROS_DISTRO=noetic
ARG DEBIAN_FRONTEND=noninteractive
ARG HOME=/root
ARG USER=root

# Cloning with ssh
# Don't forget to export docker buildkit
ENV DOCKER_BUILDKIT=1
RUN sudo apt-get install -y openssh-client git
ENV GIT_SSH_COMMAND="ssh -v"
RUN --mount=type=ssh,id=default \
    mkdir -p ~/.ssh && ssh-keyscan -H github.com >> $HOME/.ssh/known_hosts

# Install some prerequisites
RUN apt-get update && \
    apt-get install -y \
      git \
      openssh-server \
      libmysqlclient-dev \
	    bash-completion \
      ros-$ROS_DISTRO-realsense2-camera \
      ros-$ROS_DISTRO-rgbd-launch \
      ros-$ROS_DISTRO-openzen-sensor \
      ros-$ROS_DISTRO-dynamixel-workbench \
      ros-$ROS_DISTRO-rosserial-python \
      ros-$ROS_DISTRO-ompl \
      #ros-$ROS_DISTRO-mav-msgs \
      libglew-dev \
      libglfw3 \
      libglfw3-dev  \
      vim  \
      nano \
      dnsmasq  \
      libgstreamer1.0-0 \
      gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-ugly \
      gstreamer1.0-libav \
      gstreamer1.0-doc \
      gstreamer1.0-tools \
      gstreamer1.0-x \
      gstreamer1.0-alsa \
      gstreamer1.0-gl \
      gstreamer1.0-gtk3 \
      gstreamer1.0-qt5 \
      gstreamer1.0-pulseaudio \
      libgstreamer-plugins-base1.0-dev \
      libgstreamer-plugins-good1.0-dev \
      libgstreamer-plugins-bad1.0-dev \
      libgstrtspserver-1.0-dev \
      linuxptp \
      libceres-dev \
      libompl-dev

# Install prerequisites
RUN sudo apt update -y --fix-missing && \
  sudo apt install -y nmap nano ros-noetic-rosbridge-library mosquitto mosquitto-clients
RUN pip3 install inject paho-mqtt

# Install uav ros indoor
WORKDIR $HOME/$CATKIN_WORKSPACE/src
RUN --mount=type=ssh git clone git@github.com:larics/uav_ros_indoor && \
    cd uav_ros_indoor && gitman update --force && cd .. && \
    cd uav_ros_stack && gitman update --force && cd ..

RUN curl https://raw.githubusercontent.com/IntelRealSense/librealsense/master/config/99-realsense-libusb.rules >> /etc/udev/rules.d/99-realsense-libusb.rules

WORKDIR $HOME/$CATKIN_WORKSPACE/src
#RUN catkin build --continue-on-failure

ARG ROS_HOSTNAME=localhost.local
ARG ROS_MASTER_URI=http://localhost.local:11311
ARG ROS_IP=localhost.local

RUN echo " \
export ROS_HOSTNAME=$ROS_HOSTNAME" >> $HOME/.bashrc
RUN echo " \
export ROS_MASTER_URI=$ROS_MASTER_URI" >> $HOME/.bashrc
RUN echo " \
export ROS_IP=$ROS_IP" >> $HOME/.bashrc

# Install uav_ros_bridge and its dependencies
WORKDIR $HOME/$CATKIN_WORKSPACE/src
RUN --mount=type=ssh id=default && \
    git clone git@github.com:larics/mqtt_bridge.git --branch master && \
    git clone git@github.com:larics/uav_ros_bridge.git && \
    git clone git@github.com:larics/web_video_server.git && \
    git clone git@github.com:larics/async_web_server_cpp.git --branch develop
#RUN catkin build -c

RUN mkdir $HOME/bags
RUN mkdir $HOME/rosbag_default

# Prepare for startup and add autocomplete
RUN echo "export PATH=\$HOME/.local/bin:\$PATH" >> $HOME/.bashrc
RUN echo "\
if ! shopt -oq posix; then \n\
  if [ -f /usr/share/bash-completion/bash_completion ]; then \n\
    . /usr/share/bash-completion/bash_completion \n\
  elif [ -f /etc/bash_completion ]; then \n\
    . /etc/bash_completion \n\
  fi \n\
fi" >> $HOME/.bashrc
WORKDIR $HOME/$CATKIN_WORKSPACE/src/uav_ros_bridge/startup
