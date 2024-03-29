#!/bin/bash

#eval $(ssh-agent)
#export SSH_AUTH_SOCK=~/.ssh/ssh_auth_sock
export DOCKER_BUILDKIT=1
# Add ssh key and enter passphrase.
# This can be avoided if a key without passphrase is used.
#ssh-add ~/.ssh/id_ed25519
docker build \
  --ssh default \
  --build-arg ROS_HOSTNAME=$ROS_HOSTNAME \
  --build-arg ROS_MASTER_URI=$ROS_MASTER_URI \
  --build-arg ROS_IP=$ROS_IP \
  -t virtualuav_indoor_img .
