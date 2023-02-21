#!/bin/bash

# Copy the file and replace namespace accordingly. The problem with rosparam
# is that it does not support environment variables. That is why the config
# file is copied to .config and multiple parameters are changed according to
# environment variables.
cp $1 $(rospack find uav_ros_bridge)/config/.config.yaml
sed -i "s/uav_unique_namespace/${UAV_NAMESPACE}/" $(rospack find uav_ros_bridge)/config/.config.yaml

# Load rosparam here. This will ensure the parameter is loaded before running
# the mqtt communication node.
rosparam load $(rospack find uav_ros_bridge)/config/.config.yaml $UAV_NAMESPACE/mqtt_bridge