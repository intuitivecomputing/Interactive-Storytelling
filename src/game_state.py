#!/usr/bin/env python

import rospy
import smach
import smach_ros
from std_msgs.msg import Int32
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import String
import game_setting
import game_system
import arbotix_msgs.msg
from actionlib_msgs.msg import *
import json
import random
import os

class UserGameState:
    # Class to define the game state of the user

    def __init__(self,controller):
        f = open(os.path.dirname(os.path.abspath(__file__)) + '/sysSpeech.json')
        text = json.loads(f.read())
        f.close()
        self.pub_robot = rospy.Publisher('command', arbotix_msgs.msg.RobotCommand, queue_size=10)
        self.position = 0 # position on the map, start from 0
        self.cards = [] # cards that user holds
        self.game_setting = game_setting.GameSetting()
        self.state = ''
        self.system = game_system.GameSystem()
        self.controller = controller
        self.speechDict = text['speech_file']
        self.num2str = ['zero','one','two','three','four','five','six']
        self.objects = ['','camera','glasses','helicopter','phone','guitar','axe','kite','crayon','rose','scissors','FrenchFries','skateboard']
        rospy.sleep(0.2)

    def start(self):
        self.system.speak(self.speechDict['system']['intro1'])
        self.system.speak(self.speechDict['user']['role'])
        self.system.speak(self.speechDict['system']['intro2'])
        self.system.speak(self.speechDict['maki']['role'])
        self.system.speak(self.speechDict['system']['assign'])
        self.system.speak(self.speechDict['user']['assign'])
        rospy.sleep(1.5)
        self.system.speak(self.speechDict['user']['draw'])
        rospy.sleep(1.5)
        self.system.speak(self.speechDict['system']['firstCard'])
        print "in start, wait for first card"
        rospy.sleep(2.)
        card_id = rospy.wait_for_message('CARD/id', Int32MultiArray)
        self.cards.append(card_id.data[0])
        self.system.speak(self.speechDict['system']['secondCard'])
        print "in start, wait for second card"
        rospy.sleep(2.)
        while (card_id.data[0] == self.cards[-1]):
            card_id = rospy.wait_for_message('CARD/id', Int32MultiArray)
        self.cards.append(card_id.data[0])  
        self.system.speak(self.speechDict['system']['thirdCard'])
        print "in start, wait for third card"
        rospy.sleep(2.)
        while (card_id.data[0] == self.cards[-1]):
            card_id = rospy.wait_for_message('CARD/id', Int32MultiArray)
        self.cards.append(card_id.data[0]) 
        print "all cards: ", self.cards
        self.system.speak(self.speechDict['system']['finish_assign'])     



    def getCardNum(self):
        return len(self.cards)

    def getPos(self):
        return self.position

    def update(self):
        self.system.speak(self.speechDict['user']['Turn'])
        self.system.spin() # Trigger Unity Spin animation


        # Update the result after spinning
        # Need to find a way to generate
        '''
        msg = arbotix_msgs.msg.RobotCommand()
        msg_each = arbotix_msgs.msg.FloatList()
        msg.servo = []
        msg.speech = ''
        msg.face = False
        for i in range(6):
            msg_each = arbotix_msgs.msg.FloatList()
            msg_each.element = []
            if i == 4:
                msg_each.element.append(-0.3)
                msg_each.element.append(0.0)
            msg.servo.append(msg_each)
        self.pub_robot.publish(msg) # Make the robot look at the spin  
        '''
        self.controller.publisher('look at spin')

        print "in usr update, wait for SPIN/rfid"
        rfid = rospy.wait_for_message('SPIN/rfid', Int32)
        prev = rfid.data
        start = rospy.get_time()
        finish = start
        while (finish - start < 0.5):
            start = finish
            rfid = rospy.wait_for_message('SPIN/rfid', Int32)
            finish = rospy.get_time()
            print finish
        rospy.sleep(2.0)
        rfid = rospy.wait_for_message('SPIN/rfid', Int32)
        print "get SPIN/rfid"
        print "prev is : ", rfid.data
        self.position = self.position + rfid.data
        self.state = self.game_setting.getCurrentState(self.position)
        print "state is: ", self.state, " position is: ", self.position
        self.system.speak(self.speechDict['system']['spin'][self.num2str[rfid.data]])
        self.system.spin_result(self.state, rfid.data) # Trigger Unity Spin result animation
        '''
        prev = 0
        while (prev != rfid.data):
            prev = rfid.data
            try:
                print "in usr update, wait for SPIN/rfid"
                rfid = rospy.wait_for_message('SPIN/rfid', Int32, timeout = 1.5)
                print "get SPIN.rfid"
            except:
                print "prev is : ", prev
                self.position = self.position + prev
                self.state = self.game_setting.getCurrentState(self.position)
                print "state is: ", self.state, " position is: ", self.position
                self.system.speak(self.speechDict['system']['spin'][self.num2str[prev]])
                self.system.spin_result(self.state, prev) # Trigger Unity Spin result animation
        '''

    def isWin(self, end):
        # Judge whether the user has won the game
        if (self.position >= end):
            self.system.speak(self.speechDict['user']['user_win'])
        return (self.position >= end)

    def nearWin(self, end):
        # Judge whether the user will soon win

        if (end - position) < 5:
            return end - position
        else:
            return 0

    def giveCard(self):
        # Give out a card (for punishment or challenge the opponent)
        print "in usr give Card, wait for CARD/id"
        self.controller.publisher("look at card")
        card_id = rospy.wait_for_message('CARD/id', Int32MultiArray)
        print "get card_id", self.cards.index(card_id.data[0])
        self.cards.pop(self.cards.index(card_id.data[0]))
        self.system.function_card(card_id.data[0])
        self.system.speak(self.speechDict['system']['object'][self.objects[card_id.data[0]]])
        return self.objects[card_id.data[0]]

    def takeCard(self):
        # Take an extra card as prize
        print "in usr takeCard, wait for CARD/id"
        card_id = rospy.wait_for_message('CARD/id', Int32MultiArray)
        print "get card_id"
        self.controller.publisher("track")  
        self.cards.append(card_id.data[0])  
        self.system.function_card(card_id.data[0])
        self.controller.publisher("nod")  
        self.system.speak(self.speechDict['system']['object'][self.objects[card_id.data[0]]])    

    def execute(self, robot):
        rospy.sleep(3)
        self.controller.publisher("blink")  
        if self.state == 'P':
            self.execute_punishment()
        elif self.state == 'A':
            self.execute_prize()
        elif self.state == 'C':
            robot = self.execute_challenge(robot)
        else:
            pass # ERROR
        return robot

    def execute_punishment(self):
        print "in usr execute_punishmente"
        punishment = self.game_setting.generate_user('P', self.position, self.getCardNum()) # Generate punishment
        self.system.speak(self.speechDict['system']['punishment'])#(["Woops. You will be receiving punishment."]) # JSON
        if punishment == 0:
            self.position -= 2
            self.system.speak(self.speechDict['system']['punishment_goBack'])#(["Go back one step."]) # JSON
        elif punishment == 1:
            self.system.speak(self.speechDict['maki']['punishment_card'])#(["You have to give up a card. Choose one and show it to Maki."]) # JSON
            self.giveCard()
            #self.system.speak('putCard')#(["Put the card into the box."]) # JSON
        else:
            pass # ERROR CASE

    def execute_prize(self):
        print "in usr execute_prize"
        prize = self.game_setting.generate_user('A', self.position, self.getCardNum()) # Generate prize
        self.system.speak(self.speechDict['system']['award'])#(["Wow. You will receive a prize."]) # JSON

        if prize == 0:
            self.position += 2
            self.system.speak(self.speechDict['system']['award_advance'])#(["You can advance an extra step."]) # JSON
        elif prize == 1:
            self.system.speak(self.speechDict['maki']['award_card'])#(["You can have an extra card. Choose one and show it to Maki."]) # JSON
            self.takeCard()
            #self.system.speak('haveCard')#(["You can have the card."]) # JSON
        else:
            pass # ERROR CASE

    def execute_challenge(self, robot):
        #print "in usr execute_challenge"
        challenge = self.game_setting.generate_user('C', self.position, self.getCardNum()) # Generate challenge
        self.system.speak(self.speechDict['system']['challenge1'])#(["Come on. Take the challenge."]) # JSON
        self.system.speak(challenge['name'])
        self.system.speak(self.speechDict['system']['challenge2'])#(["Come on. Take the challenge."]) # JSON
        print "in usr execute challenge, wait for CHOICE String"
        try:
            choice = rospy.wait_for_message('CHOICE', String, timeout=10.0) # 0 stands for giving up challenge; 1 stands for accept challenge
        except:
            self.system.speak(self.speechDict['system']['choose'])
            choice = rospy.wait_for_message('CHOICE', String)
        print "get CHOICE String"

        if (choice.data == '0'): # Give up
            self.position -= 2
            #s = 'chlgPunish' + self.num2str[challenge['punishment']] + 'step'
            self.system.speak(self.speechDict['system']['punishment_goBack']) 

        elif (choice.data == '1'): # Accept challenge
            #self.system.speak('bravo')#(['Bravo.']) # JSON
            obj = ''
            if (robot.getCardNum() > 0):
                self.system.speak(self.speechDict['user']['challenge_user'])#(['Maki. Do you want to give a challenge card?']) # JSON
                obj = robot.giveCard()
                self.system.speak(self.speechDict['system']['include'])
            else:
                self.system.speak(self.speechDict['user']['runOut_maki'])

            start = rospy.get_time() # Mark when the user starts speaking
            print "in usr execute_challenge, wait for FINISHED string"
            rospy.wait_for_message('FINISHED', String)
            print "get FINISHED string"
            finish = rospy.get_time() # Mark when the user finishes speaking
            self.system.speak(self.speechDict['system']['analyze'])
            self.system.speak(self.speechDict['system']['analyzing'])
            print "Time elaspe", finish - start
            if (finish - start > 20): # Decide whether the story is long enough to determine whether passing the challenge
                self.position += 3 # reward
                self.controller.publisher("nod")  
                #s = 'succeed' + self.num2str[challenge['reward']] + 'step'
                self.system.speak(self.speechDict['system']['success'])

            else:
                #s = 'fail' + self.num2str[challenge['reward']] + 'step'
                self.system.speak(self.speechDict['system']['fail'])                
        else:
            pass # Error Case

        return robot
    


class RobotGameState:
    # Class to define the game state of the robot

    def __init__(self,controller):
        f = open(os.path.dirname(os.path.abspath(__file__)) + '/sysSpeech.json')
        text = json.loads(f.read())
        f.close()
        self.speechDict = text['speech_file']
        self.position = 0 # position on the map, start from 0
        self.state = ''
        self.cards = [7,8,9] # cards that robot holds 
        self.extra_cards = [10,11,12]
        self.system = game_system.GameSystem()
        self.game_setting = game_setting.GameSetting()
        self.steps = [1,2,3,4,5]
        self.controller = controller
        self.num2str = ['zero','one','two','three','four','five','six']

        self.objects = ['','camera','glasses','helicopter','phone','guitar','axe','kite','crayon','rose','scissors','FrenchFries','skateboard']



    def getCardNum(self):
        return len(self.cards)

    def isWin(self, end):
        # Judge whether the robot has won the game
        if (self.position >= end):
            self.system.speak(self.speechDict['system']['maki_win'])
        return (self.position > end)

    def nearWin(self, end):
        # Judge whether the robot will soon win

        if (end - self.position) < 5:
            return end - self.position
        else:
            return 0

    def giveCard(self):
        # Give out a card (for punishment or challenge the opponent)

        card_id = self.cards.pop(0)
        print "in robot giveCard ", card_id
        self.system.function_card(card_id)
        self.system.speak(self.speechDict['system']['object'][self.objects[card_id]])
        return self.objects[card_id]


    def takeCard(self):
        # Take an extra card as prize
        card_id = self.extra_cards.pop(0)
        print "in robot takeCard ", card_id
        self.cards.append(card_id)  
        self.system.function_card(card_id)
        self.system.speak(self.speechDict['system']['object'][self.objects[card_id]])


    def update(self, user):
        print "in robot update"
        if (user.getPos() - self.position < -2):
            spin = random.choice(self.steps[:2])
        elif (user.getPos() - self.position > 2):
            spin = random.choice(self.steps[2:])
        else:
            spin = random.choice(self.steps)

        self.system.speak(self.speechDict['maki']['Turn'])#(["Spin the wheel and wish for good luck"]) # JSON
        self.controller.publisher('start_spin')
        self.system.spin()
        rospy.wait_for_message('ROBOT/done',String)
        rospy.sleep(1.2)
        self.controller.publisher('stop_spin')
        rospy.sleep(2)
        self.system.speak(self.speechDict['system']['spin'][self.num2str[spin]])
        self.position = self.position + spin
        self.state = self.game_setting.getCurrentState(self.position)
        self.system.spin_result(self.state, spin) # Trigger Unity Spin result animation

    def execute(self, user):
        rospy.sleep(3)
        if self.state == 'P':
            self.execute_punishment()
        elif self.state == 'A':
            self.execute_prize()
        elif self.state == 'C':
            user = self.execute_challenge(user)
        else:
            pass # ERROR
        return user

    def execute_punishment(self):
        print "in robot execute_punishment"
        punishment = self.game_setting.generate_robot('P', self.position, self.getCardNum()) # Generate punishment
        self.system.speak(self.speechDict['system']['punishment'])#(["Woops. You will be receiving punishment."]) # JSON

        if punishment == 0:
            self.position -= 2
            self.system.speak(self.speechDict['system']['punishment_goBack'])#(["Go back one step."]) # JSON
        elif punishment == 1:
            self.system.speak(self.speechDict['user']['punishment_card'])#(["You have to give up a card. Choose one and show it to Maki."]) # JSON
            self.giveCard()
            #self.system.speak('putCard')#(["Put the card into the box."]) # JSON
        else:
            pass # ERROR CASE

    def execute_prize(self):
        print "in robot execute_prize"
        prize = self.game_setting.generate_robot('A', self.position, self.getCardNum()) # Generate prize
        self.system.speak(self.speechDict['system']['award'])#(["Wow. You will receive a prize."]) # JSON

        if prize == 0:
            self.position += 2
            self.system.speak(self.speechDict['system']['award_advance'])#(["You can advance an extra step."]) # JSON
        elif prize == 1:
            self.system.speak(self.speechDict['user']['award_card'])#(["You can have an extra card. Choose one and show it to Maki."]) # JSON
            self.takeCard()
            #self.system.speak('haveCard')#(["You can have the card."]) # JSON
        else:
            pass # ERROR CASE

    def execute_challenge(self, user):
        #print "in robot execute_challenge"
        challenge = self.game_setting.generate_robot('C', self.position, self.getCardNum()) # Generate challenge
        self.system.speak(self.speechDict['system']['challenge1'])#(["Come on. Take the challenge."]) # JSON
        self.system.speak(challenge['name'])
        self.system.speak(self.speechDict['system']['challenge2'])#(["Come on. Take the challenge."]) # JSON
        print "in robot execute_challenge, wait for ROBOT/done string"
        self.controller.publisher('take_challenge')
        rospy.wait_for_message('ROBOT/done',String)      
        choice = 1
        print "get CHOICE string"
        if (choice == 0): # Give up
            self.position -= 2
            #s = 'chlgPunish' + self.num2str[challenge['punishment']] + 'step'
            self.system.speak(self.speechDict['system']['punishment_goBack']) 

        elif (choice == 1): # Accept challenge
            #self.system.speak('bravo')#(['Bravo.']) # JSON
            obj = ''
            if (user.getCardNum() > 0):
                self.system.speak(self.speechDict['user']['challenge_maki'])#(['Maki. Do you want to give a challenge card?']) # JSON
                obj = user.giveCard()
                self.system.speak((self.speechDict['system']['include']))
            else:
                self.system.speak(self.speechDict['user']['runOut_user'])

            start = rospy.get_time() # Mark when the user starts speaking
            print "in robot execute_challenge, wait for FINISHED string"
            self.controller.storyPublisher(challenge['name'],obj)
            rospy.wait_for_message('ROBOT/done',String)
            rospy.sleep(0.3)  
            self.controller.publisher('story_finish')
            rospy.wait_for_message('ROBOT/done',String)   
            print "get FINISHED String"
            finish = rospy.get_time() # Mark when the user finishes speaking
            self.system.speak(self.speechDict['system']['analyze'])
            self.system.speak(self.speechDict['system']['analyzing'])
            if (finish - start > 20): # Decide whether the story is long enough to determine whether passing the challenge
                self.position += 3 # reward
                #s = 'succeed' + self.num2str[challenge['reward']] + 'step'
                self.system.speak(self.speechDict['system']['success'])

            else:
                #s = 'fail' + self.num2str[challenge['reward']] + 'step'
                self.system.speak(self.speechDict['system']['fail'])               
        else:
            pass # Error Case

        return user












