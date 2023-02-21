#!/usr/bin/env python
import json
import yaml
import sys
import importlib

def msg2json(msg):
    ''' Convert a ROS message to JSON format'''
    y = yaml.load(str(msg))
    return json.dumps(y,indent=2)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        msgs = importlib.import_module(sys.argv[1] + '.msg')
        msg = getattr(msgs, sys.argv[2])
        P = msg()
        print(msg2json(P))
    else:
        print("Please provide message module and message type to be serialized.")
        print("Example:")
        print("rosrun mqtt_bridge ros2json_serializer.py geometry_msgs Point")


    #msgs = __import__(sys.argv[1] + ".msg")
    #print(msgs.msg.Point)
    #P = getattr(msgs.msg, sys.argv[2])
    #P = msgs.msg.Point()
    #print msg2json(P)
    #from geometry_msgs.msg import PoseStamped
    #P = PoseStamped()
    #print msg2json(P)