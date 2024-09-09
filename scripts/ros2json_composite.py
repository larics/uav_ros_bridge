#!/usr/bin/env python
import json
import yaml
import sys
import importlib
import copy
from uav_ros_msgs.msg import Waypoint, Waypoints, Task
from pcl_ris_msgs.msg import InspectionTrajectoryGui
from geometry_msgs.msg import Pose
from std_msgs.msg import Float64MultiArray, MultiArrayDimension

def msg2json(msg):
    ''' Convert a ROS message to JSON format'''
    y = yaml.load(str(msg))
    return json.dumps(y,indent=2)

def createInspectionTrajectoryGuiExample(n):
    traj = InspectionTrajectoryGui()
    for i in range(n):
        pose = Pose()
        pose.position.x = i
        traj.poses.append(pose)
    
    matrix = [
        [1.0, 2.0, 3.0, 4.0],
        [5.0, 6.0, 7.0, 8.0],
        [9.0, 10.0, 11.0, 12.0],
        [13.0, 14.0, 15.0, 16.0]
    ]

    # Set up dimensions for a 4x4 matrix
    dim_row = MultiArrayDimension()
    dim_row.label = "rows"
    dim_row.size = 4
    dim_row.stride = 4 * 4  # Total number of elements (4x4)

    dim_col = MultiArrayDimension()
    dim_col.label = "columns"
    dim_col.size = 4
    dim_col.stride = 4

    traj.transform.layout.dim = [dim_row, dim_col]

    # Flatten the matrix and assign the data
    traj.transform.data = [elem for row in matrix for elem in row]  # Flattening the matrix row-wise

    return traj

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

    # InspectionTrajectory
    print("Inspection trajectory GUI message")
    print(msg2json(createInspectionTrajectoryGuiExample(2)))