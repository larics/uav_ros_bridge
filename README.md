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



## Video streaming
Install following packages to use the video stream:

```bash
cd ~/catkin_ws
git clone https://github.com/larics/web_video_server.git
git clone https://github.com/larics/async_web_server_cpp.git
cd async_web_server_cpp
git checkout noetic-devel
catkin build web_video_server async_web_server_cpp
```

To run the video stream, simply run:
```bash
rosrun web_video_server web_video_server
```

Go to your browser and connect to `localhost:8080`, or `<machine_ip>:8080` if you are connecting from another device. All raw image topics will be listed. If you want to connect to a compressed image topic, go to following in your browser: [http://localhost:8080/stream?topic=/usb_cam/image_raw&type=ros_compressed](http://localhost:8080/stream?topic=/usb_cam/image_raw&type=ros_compressed)


Use the compressed image to limit the bandwidth.


## Useful stuff
To view the mqtt messages sent through the system, you can use `mqtt_explorer`.