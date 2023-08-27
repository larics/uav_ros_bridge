FROM lmark1/uav_ros_simulation:focal

# Use ARG - persists only during docker build
# https://github.com/moby/moby/issues/4032#issuecomment-192327844
ARG CATKIN_WORKSPACE=uav_ws
ARG DEBIAN_FRONTEND=noninteractive
ARG HOME=/root
ARG USER=root

# Cloning with ssh
# Don't forget to export docker buildkit
ENV DOCKER_BUILDKIT=1
RUN sudo apt-get install -y openssh-client
ENV GIT_SSH_COMMAND="ssh -v"
RUN --mount=type=ssh,id=default \
    mkdir -p ~/.ssh && ssh-keyscan -H github.com >> $HOME/.ssh/known_hosts

# Install uav_ros_bridge and its dependencies
WORKDIR $HOME/$CATKIN_WORKSPACE/src
RUN --mount=type=ssh id=default && \
    git clone git@github.com:larics/mqtt_bridge.git --branch 0.1.7 && \
    git clone git@github.com:larics/uav_ros_bridge.git
RUN catkin build -c

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
WORKDIR $HOME/$CATKIN_WORKSPACE/src/uav_ros_bridge/startup/uav_sim_example