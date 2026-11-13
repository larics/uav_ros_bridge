#!/bin/bash
# The MQTT adapter with the fake backend, its photos on the fake camera and a local mosquitto,
# no simulator: once with the plain schema, once with the example profile, then across a
# broker restart. Starts a master of its own.
#   test/drone_interface_mqtt_check.sh
HERE=$(dirname "$(readlink -f "$0")")
PKG=$(readlink -f "$HERE/..")
PORT=18884
MEDIA_PORT=18081
# check_util.py and .sh, shared with the drone interface checks
CHECKS=$(rospack find uav_ros_general)/test/drone_interface
export PYTHONPATH="$CHECKS${PYTHONPATH:+:$PYTHONPATH}"
source "$CHECKS/check_util.sh"
export UAV_NAMESPACE=check
start_master 11395 '$ADAPTER $NODE $CAMERA $MEDIA $BROKER'
mosquitto -p $PORT > /dev/null 2>&1 &
BROKER=$!
roslaunch uav_ros_general drone_interface.launch backend:=uav_ros_general/FakeBackend \
  > /tmp/drone_interface_mqtt_node.log 2>&1 &
NODE=$!
ROS_NAMESPACE=$UAV_NAMESPACE rosrun uav_ros_general fake_camera_node.py > /dev/null 2>&1 &
CAMERA=$!
roslaunch uav_ros_general camera_media.launch image_topic:=fake_camera/image_raw stream:=false \
  media_port:=$MEDIA_PORT photo_dir:="$WORK" \
  > /tmp/drone_interface_mqtt_media.log 2>&1 &
MEDIA=$!
roslaunch uav_ros_bridge drone_interface_mqtt_adapter.launch port:=$PORT > /tmp/drone_interface_mqtt_adapter.log 2>&1 &
ADAPTER=$!
python3 "$HERE/drone_interface_mqtt_check.py" $PORT drone/vehicle plain
RESULT=$?
kill $ADAPTER; sleep 2
roslaunch uav_ros_bridge drone_interface_mqtt_adapter.launch port:=$PORT \
  profile:="$PKG/config/drone_interface/profiles/example.yaml" > /tmp/drone_interface_mqtt_adapter2.log 2>&1 &
ADAPTER=$!
python3 "$HERE/drone_interface_mqtt_check.py" $PORT drone/vehicle profile
RESULT=$((RESULT + $?))
# A broker without persistence forgets the retained capabilities when it restarts
kill $BROKER; wait $BROKER 2>/dev/null
mosquitto -p $PORT > /dev/null 2>&1 &
BROKER=$!
python3 "$HERE/drone_interface_mqtt_check.py" $PORT drone/vehicle restart
exit $((RESULT + $?))
