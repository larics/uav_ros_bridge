cmake_minimum_required(VERSION 2.8.3)
project(uav_ros_bridge)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  trajectory_msgs
  nav_msgs
)

#add_message_files(
#  FILES
#  file.msg
#)

#add_service_files(
#  FILES
#  file.srv
#)

catkin_package(
  INCLUDE_DIRS
  LIBRARIES
  CATKIN_DEPENDS
  DEPENDS
)