#!/usr/bin/env python

import rospy
import smach
import smach_ros
from std_msgs.msg import Int32
from std_msgs.msg import String
import game_setting
import actionlib
from sound_play.msg import SoundRequest, SoundRequestAction, SoundRequestGoal
from watson_developer_cloud import TextToSpeechV1
import roslib; roslib.load_manifest('sound_play')
import os
import json
from sets import Set

class GameSystem:
    def __init__(self):

        self.pub_rotate = rospy.Publisher('rotate', String, queue_size=10)
        self.pub_rotate_result = rospy.Publisher('rotate_result', String, queue_size=10)
        self.pub_function = rospy.Publisher('function_card', String, queue_size=10)

        self.client =  actionlib.SimpleActionClient('sound_play', SoundRequestAction)
        self.cards = ['','camera','glasses','helicopter','phone','guitar','axe','kite','crayon','rose','scissors','FrenchFries','skateboard']
        self.soundPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/sysAudio/"

    def spin(self):
        msg = String()
        msg.data = 'X'
        self.pub_rotate.publish(msg)

    def spin_result(self, state, result):
        msg = String()
        s = ''
        s += state
        s += str(result)
        msg.data = s
        self.pub_rotate_result.publish(msg)

    def function_card(self,idx):
        # Publish card result to Unity
        msg = String()
        msg.data = self.cards[idx]
        self.pub_function.publish(msg)
        rospy.sleep(1.5)

    def speak(self, audioPath):
        self.client.wait_for_server()
        try:
            goal = SoundRequestGoal()
            goal.sound_request.sound = SoundRequest.PLAY_FILE
            goal.sound_request.command = SoundRequest.PLAY_ONCE
            goal.sound_request.arg = self.soundPath + audioPath + ".wav"
            goal.sound_request.volume = 1.0
            self.client.send_goal(goal)
            self.client.wait_for_result()
        except:
            print "print " + audioPath + "fails"   


        

