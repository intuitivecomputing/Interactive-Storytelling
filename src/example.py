#!/usr/bin/env python

import rospy
rospy.init_node('example', anonymous=True)
import smach
import smach_ros
from std_msgs.msg import Int32
import game_state
import game_controller
import signal
import sys





c = game_controller.RobotController()
s = game_state.UserGameState(c)
r = game_state.RobotGameState(c)

i = 0

def sigint_handler(signum, frame):
    import actionlib
    from sound_play.msg import SoundRequest, SoundRequestAction, SoundRequestGoal
    client =  actionlib.SimpleActionClient('sound_play', SoundRequestAction)
    client.wait_for_server()
    goal = SoundRequestGoal()
    goal.sound_request.sound = SoundRequest.PLAY_FILE
    goal.sound_request.command = SoundRequest.PLAY_ONCE
    goal.sound_request.arg = ""
    goal.sound_request.volume = 1.0
    self.client.send_goal(goal)
    exit(0)

#signal.signal(signal.SIGINT, sigint_handler)

s.start()

while not s.isWin(20):
	print "round ", i
	i = i + 1
	s.update()
	if (s.isWin(20)):
		break
	s.execute(r)
	if (s.isWin(20)):
		break
	r.update(s)
	if (r.isWin(20)):
		break
	r.execute(s)
	if (r.isWin(20)):
		break
