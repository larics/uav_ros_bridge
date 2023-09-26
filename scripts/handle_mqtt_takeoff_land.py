#!/usr/bin/env python

__author__ = 'aivanovic'

import rospy
from std_msgs.msg import Bool
from std_srvs.srv import SetBool, SetBoolRequest, SetBoolResponse
from uav_ros_msgs.srv import TakeOff, TakeOffRequest, TakeOffResponse
from mavros_msgs.srv import CommandBool, CommandBoolRequest, CommandBoolResponse


class HandleTakeoffLand:

  def __init__(self):
    
    # Set up parameters
    self.takeoff_rel_alt = rospy.get_param('~takeoff_relative_height', 2.0)

    # Set up services for takeoff and land and arming
    self.armingService = rospy.ServiceProxy('handle_mqtt_takeoff_land/service/arm', CommandBool)
    self.takeoffService = rospy.ServiceProxy('handle_mqtt_takeoff_land/service/takeoff', TakeOff)
    self.landService = rospy.ServiceProxy('handle_mqtt_takeoff_land/service/land', SetBool)

    # Set up subscribers for mqtt topics
    rospy.Subscriber('handle_mqtt_takeoff_land/takeoff', Bool, self.takeoffCallback,
      queue_size=1)
    rospy.Subscriber('handle_mqtt_takeoff_land/land', Bool, self.landCallback,
      queue_size=1)
    rospy.Subscriber('handle_mqtt_takeoff_land/arm', Bool, self.armCallback,
      queue_size=1)
    
  def run(self):
    rospy.spin()
  
  def takeoffCallback(self, msg):
    print("Takeoff")
    req = TakeOffRequest()
    req.rel_alt = self.takeoff_rel_alt
    res = self.takeoffService.call(req)

    print("Takeoff service executed with: " + str(res.success) + ", with message: " + res.message)
  
  def landCallback(self, msg):
    print("Land")
    req = SetBoolRequest()
    req.data = msg.data
    res = self.landService(req)

    print("Land service executed with: " + str(res.success) + ", with message: " + res.message)

  def armCallback(self, msg):
    print("Arm")
    req = CommandBoolRequest()
    req.value = msg.data
    res = self.armingService(req)

    print("Arming service executed with: " + str(res.success) + ", with message: " + str(res.result))

if __name__ == '__main__':
  rospy.init_node('handle_mqtt_takeoff_land')
  tl = HandleTakeoffLand()
  tl.run()
