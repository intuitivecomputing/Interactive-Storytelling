#!/usr/bin/env python

import rospy
import os
#import game_state
import game_system
rospy.init_node('testAudio', anonymous=True)
s = game_system.GameSystem()
audioList = os.listdir("/home/intuitive-computing/catkin_ws/src/arbotix_ros/interactive_storytelling/sysAudio")
#print audioList
audioList = map(lambda x: x[:-4], audioList)
#print audioList
i = 0
#s.speak(audioList[0])

while i < 200: 
	for x in audioList:
		#x = "say-beep"
		i = i+1
		print i, "th audio: ", x
		s.speak(x)
		print i, "th speak finished"
		


