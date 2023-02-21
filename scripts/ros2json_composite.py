#!/usr/bin/env python
import json
import yaml
import sys
import importlib
import copy
from uav_ros_msgs.msg import Waypoint, Waypoints, Task

def msg2json(msg):
    ''' Convert a ROS message to JSON format'''
    y = yaml.load(str(msg))
    return json.dumps(y,indent=2)

if __name__ == "__main__":
    task = Task()
    waypoint = Waypoint()
    waypoints = Waypoints()

    # waypoint with one task
    task.id = 1
    waypoint.tasks.append(copy.deepcopy(task))
    waypoint.waiting_time = 1.0
    waypoints.waypoints.append(copy.deepcopy(waypoint))
    print("Waypoint with single task")
    print(msg2json(waypoint))

    # waypoint with two tasks
    waypoint = Waypoint()
    task.id = 2
    waypoint.tasks.append(copy.deepcopy(task))
    task.id = 3
    waypoint.tasks.append(copy.deepcopy(task))
    waypoint.waiting_time = 2.0
    waypoints.waypoints.append(copy.deepcopy(waypoint))
    print("Waypoint with two tasks")
    print(msg2json(waypoint))

    print("Waypoints message")
    print(msg2json(waypoints))