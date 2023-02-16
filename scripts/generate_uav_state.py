#!/usr/bin/env python

__author__ = 'aivanovic'

import rospy
from geometry_msgs.msg import Pose, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32, Header
from sensor_msgs.msg import Imu, BatteryState
from uav_ros_bridge.msg import UavState


class GenerateUavState:

  def __init__(self):
    # Published message rate
    self.rate = rospy.get_param('~rate', 20)
    # Min and max voltage
    self.voltage_min = rospy.get_param('~voltage/min', 21.3)
    self.voltage_max = rospy.get_param('~voltage/max', 25.2)

    # Composite message to publish
    self.uav_state = UavState()
    self.uav_state_pub = rospy.Publisher('generate_uav_state/uav_state',
      UavState, queue_size=1)

    # Subscribers
    self.odometry = Odometry()
    rospy.Subscriber('generate_uav_state/odometry', Odometry, self.odometryCallback,
      queue_size=1)

    self.imu = Imu()
    rospy.Subscriber('generate_uav_state/imu', Imu, self.imuCallback,
      queue_size=1)

    self.battery_state = BatteryState()
    rospy.Subscriber('generate_uav_state/battery_state', BatteryState,
      self.batteryStateCallback, queue_size=1)

  def run(self):
    rate = rospy.Rate(self.rate)
    while not rospy.is_shutdown():
      rate.sleep()

      # Data from odometry
      self.uav_state.pose = self.odometry.pose.pose
      self.uav_state.velocity = self.odometry.twist.twist

      # Add angular velocity and linear acceleration in message
      self.uav_state.velocity.angular = self.imu.angular_velocity
      self.uav_state.acceleration.linear = self.imu.linear_acceleration

      # Battery stuff
      self.uav_state.battery_voltage = self.battery_state.voltage
      self.uav_state.battery_percentage = (1 - 
        (self.voltage_max - self.battery_state.voltage)/(self.voltage_max - self.voltage_min))*100

      # Append stamp
      self.uav_state.header.stamp = rospy.Time.now()

      # Publish state
      self.uav_state_pub.publish(self.uav_state)

  def odometryCallback(self, msg):
    self.odometry = msg

  def imuCallback(self, msg):
    self.imu = msg

  def batteryStateCallback(self, msg):
    self.battery_state = msg


if __name__ == '__main__':
  rospy.init_node('generate_uav_state')
  gs = GenerateUavState()
  gs.run()
