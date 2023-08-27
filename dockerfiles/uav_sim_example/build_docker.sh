#!/bin/bash

#eval $(ssh-agent)
#export SSH_AUTH_SOCK=~/.ssh/ssh_auth_sock
export DOCKER_BUILDKIT=1
# Add ssh key and enter passphrase.
# This can be avoided if a key without passphrase is used.
ssh-add ~/.ssh/id_ed25519
docker build --ssh default -t uav_sim_bridge_img .