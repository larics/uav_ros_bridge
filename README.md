# uav_ros_bridge
Uav communication over mqtt


## Installation
First install following prerequisites in your catkin workspace:
```bash
cd ~/catkin_ws/src
git clone git@github.com:larics/mqtt_bridge.git
cd mqtt_bridge
git checkout 0.1.7
catkin build
```

Clone this package in your catkin workspace and build.
```bash
cd ~/catkin_ws/src
git clone git@github.com:larics/uav_ros_bridge.git
catkin build uav_ros_bridge
```

## Running

### Demo mqtt
To start demo simply run:
```bash
rosrun uav_ros_bridge demo.launch
```

This launch file sends only one topic over mqtt server. To start the broadcast publish following:
```bash
rostopic pub -r 20 /uav/pose geometry_msgs/Pose "position:
  x: 0.0
  y: 0.0
  z: 0.0
orientation:
  x: 0.0
  y: 0.0
  z: 0.0
  w: 1.0"
```



## Useful stuff
To view the mqtt messages sent through the system, you can use `mqtt_explorer`.