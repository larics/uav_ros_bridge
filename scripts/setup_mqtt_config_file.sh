#!/bin/bash

# Copy the file and replace namespace accordingly. The problem with rosparam
# is that it does not support environment variables. That is why the config
# file is copied to .config and multiple parameters are changed according to
# environment variables.
CFG_FILE=$(rospack find uav_ros_bridge)/config/.config.yaml
cp $1 $CFG_FILE
sed -i "s/uav_unique_namespace/${UAV_NAMESPACE}/" $CFG_FILE

# Change ip address for the mqtt server if available.
if [ -z "$UAV_IP" ]
then
  #echo "\$UAV_IP is empty. Defaulting to localhost."
  sed -i "s/host: uav_unique_ip/host: localhost/" $CFG_FILE
else
  #echo "\$UAV_IP is NOT empty. IP will be set to $UAV_IP."
  sed -i "s/host: uav_unique_ip/host: ${UAV_IP}/" $CFG_FILE
fi
# Load rosparam here. This will ensure the parameter is loaded before running
# the mqtt communication node.
rosparam load $CFG_FILE $UAV_NAMESPACE/mqtt_bridge

