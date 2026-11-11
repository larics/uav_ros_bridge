#!/bin/bash
# The MQTT adapter with the fake backend and a local mosquitto, no simulator: once with the
# plain schema, once with the example profile.
#   test/drone_interface_mqtt_check.sh
HERE=$(dirname "$(readlink -f "$0")")
PKG=$(readlink -f "$HERE/..")
PORT=18884
# check_util.py, shared with the drone interface checks
export PYTHONPATH="$(rospack find uav_ros_general)/test/drone_interface${PYTHONPATH:+:$PYTHONPATH}"
export UAV_NAMESPACE=check
roscore > /dev/null 2>&1 &
CORE=$!
mosquitto -p $PORT > /dev/null 2>&1 &
BROKER=$!
trap 'kill $ADAPTER $NODE $BROKER $CORE 2>/dev/null; wait 2>/dev/null' EXIT
until rostopic list > /dev/null 2>&1; do sleep 0.2; done
roslaunch uav_ros_general drone_interface.launch backend:=uav_ros_general/FakeBackend > /tmp/drone_interface_mqtt_node.log 2>&1 &
NODE=$!
roslaunch uav_ros_bridge drone_interface_mqtt_adapter.launch port:=$PORT > /tmp/drone_interface_mqtt_adapter.log 2>&1 &
ADAPTER=$!
python3 "$HERE/drone_interface_mqtt_check.py" $PORT drone/vehicle plain
RESULT=$?
kill $ADAPTER; sleep 2
roslaunch uav_ros_bridge drone_interface_mqtt_adapter.launch port:=$PORT \
  profile:="$PKG/config/drone_interface/profiles/example.yaml" > /tmp/drone_interface_mqtt_adapter2.log 2>&1 &
ADAPTER=$!
python3 "$HERE/drone_interface_mqtt_check.py" $PORT drone/vehicle profile
exit $((RESULT + $?))
