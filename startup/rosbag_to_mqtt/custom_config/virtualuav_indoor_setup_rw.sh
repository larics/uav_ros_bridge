#!/bin/bash

IFACE=$(netstat -i | awk '{print $1}' | grep w)
export UAV_IP=$(ifconfig $IFACE | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
# Global Planner parameters
#export ABSOLUTE_CONFIG=true
#export MAP_CONFIG=$(rospack find icuas23_competition)/config/global_planner.yaml
#export TRAJ_CONFIG=$(rospack find icuas23_competition)/config/global_planner.yaml
#export STATE_VALIDITY_CONFIG=$(rospack find icuas23_competition)/config/global_planner.yaml
#export PATH_PLANNER_CONFIG=$(rospack find icuas23_competition)/config/global_planner.yaml
#export MODEL_CORRECTION_CONFIG=$(rospack find larics_motion_planning)/config/model_correction_config_example.yaml

# Empty map
# export OCTOMAP_FILE=$(rospack find larics_motion_planning)/config/empty_map.binvox.bt

# Uncomment this if using a real map
# export OCTOMAP_FILE=$(pwd)/custom_config/icuas2022_arena_latest.binvox.bt
#export OCTOMAP_FILE=$(rospack find icuas_support)/resources/arena_warszawa_2.binvox.bt

# Optitrack parameters
export OBJECT_NAME=falconblack
export ODOM_TOPIC=/$OBJECT_NAME/vrpn_client/estimated_odometry
export OPTITRACK_IP=192.168.1.50
#export GEOFENCE_CONFIG=$(pwd)/custom_config/geofence_config.yaml

# Pixhawk
export UAV_NAMESPACE=red
export PIX_SYM=/dev/ttyUSB_px4:921600
export MAP_FRAME=optitrack

# Camera parameters
export CAMERA_LINK=$UAV_NAMESPACE/camera
export BASE_LINK=$UAV_NAMESPACE/base_link

export TEAM_NAME=SDNCLAB

