#!/usr/bin/env python

import rospy
from std_msgs.msg import Int32
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import String
import arbotix_msgs.msg
from actionlib_msgs.msg import *
import json
import random
import os


class RobotController:
    # class to process robot controller

    def __init__(self):

        #JSON
        f = open(os.path.dirname(os.path.abspath(__file__)) + "/robot_action.json")
        self.action = json.loads(f.read())
        f.close()

        f = open(os.path.dirname(os.path.abspath(__file__)) + "/story.json")
        self.story = json.loads(f.read())
        f.close()

        self.pub_robot = rospy.Publisher('command', arbotix_msgs.msg.RobotCommand, queue_size=10)

    def publisher(self,command):
        msg = arbotix_msgs.msg.RobotCommand()
        servo = self.action[command]['servo']
        msg.speech = self.action[command]['speech']
        msg.face = self.action[command]['face']
        msg.servo = []
        for i in range(6):
            msg_each = arbotix_msgs.msg.FloatList()
            msg_each.element = servo[i]
            msg.servo.append(msg_each)
        self.pub_robot.publish(msg)

    def storyPublisher(self,setting,objects):
        msg = arbotix_msgs.msg.RobotCommand()
        servo = self.action['track']['servo']
        msg.face = False
        msg.speech = self.story['storyFile'][setting][objects]
        msg.servo = []
        for i in range(6):
            msg_each = arbotix_msgs.msg.FloatList()
            msg_each.element = servo[i]
            msg.servo.append(msg_each)
        self.pub_robot.publish(msg)