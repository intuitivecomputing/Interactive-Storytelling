#!/usr/bin/env python
import json
import rospy
import smach
import smach_ros
from std_msgs.msg import Int32
import os

class GameSetting:
    # Class to define the game setting

    def __init__(self): #filename is name of json file
        f = open(os.path.dirname(os.path.abspath(__file__)) + '/sysSetting.json','r')
        text = json.loads(f.read())
        f.close()
        self.map = text['map'] # JSON
        #self.map = ['C','C','C','P','C','C','C','A','C','C','P','C','C','A','C','A','C','C','P','C']
        self.setting_usr = text['setting_usr'] # JSON
        self.setting_sys = text['setting_sys']
        self.visited_usr = 0 # Story settings that users have already encountered
        self.visited_sys = 0

    def getCurrentState(self, position):
        # Get current state for the user (challenge, punishment, prize)
        return self.map[position]

    def generate_user(self, state, user_pos, user_cards):
        # Take the state (challenge, punishment, prize) and generates an instance

        if state == 'C': # challenge
            self.visited_usr += 1
            return self.setting_usr[self.visited_usr - 1]

        elif state == 'P': # punishment
            if (user_cards > 1):
                return 1 # Punishment1 : give up a card
            else:
                return 0

        elif state == 'A': # prize
            if (user_cards > 1):
                return 0 # Prize0 : Advance one step
            else:
                return 1 # Prize1 : Get another card

        else:
            pass # ERROR CASE

    def generate_robot(self, state, user_pos, user_cards):
        # Take the state (challenge, punishment, prize) and generates an instance

        if state == 'C': # challenge
            self.visited_sys += 1
            return self.setting_sys[self.visited_sys - 1]

        elif state == 'P': # punishment
            if (user_cards > 1):
                return 1 # Punishment1 : give up a card
            else:
                return 0

        elif state == 'A': # prize
            if (user_cards > 1):
                return 0 # Prize0 : Advance one step
            else:
                return 1 # Prize1 : Get another card

        else:
            pass # ERROR CASE