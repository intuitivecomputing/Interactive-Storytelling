#!/usr/bin/env python

import rospy
import smach
import smach_ros
import arbotix_msgs
import arbotix_python
from std_msgs.msg import Int32
from std_msgs.msg import Empty
from std_msgs.msg import Int32MultiArray


def monitor_FACE_MONITOR_cb(ud, msg):
    ud.FACE_MONITOR_output = msg.data
    return False

#------------------------------------------------

class FACE_PROCESSOR_state(smach.State):
    def __init__(self):
        smach.State.__init__(self, 
                             outcomes=['preempted','continue'],
                             input_keys=['FACE_PROCESSOR_input'],
                             output_keys=['FACE_PROCESSOR_output'])
        self.face_postion = [0, 0]
        self.move_threshold = 100
    #--------------------------------NEED MODIFY (CALIBRATION)
    def coordinate2servo(self, x, y):
        if x < 300:
            servo6 = -2.6
        elif x < 450:
            servo6 =  -2.3
        else:
            servo6 = -2.0

        if y < 250:
            servo5 = 0.0
        else:
            servo5 = -0.2

        return [servo5, servo6]
    #--------------------------------
    def execute(self, userdata):
        if self.preempt_requested():
            self.service_preempt()
            return 'preempted'

        # Compare with previous face postion to see if the face position has moved
        [x, y] = userdata.FACE_PROCESSOR_input
        distance = (self.face_postion[0] - x) ** 2 + (self.face_postion[1] - y) ** 2
        if (distance > self.move_threshold):
            userdata.FACE_PROCESSOR_output = self.coordinate2servo(x, y)
        return 'continue'
#-----------------------------------------------------------------------------------------

sm_FACE_TRACKER = smach.StateMachine(outcomes=['FACE_TRACKER_exit','FACE_TRACKER_continue'],
	                                 output_keys=['FACE_TRACKER_MODULE_output'])
sm_FACE_TRACKER.userdata.FACE_data = [0, 0]
with sm_FACE_TRACKER:
    smach.StateMachine.add('FACE_MONITOR',
                           smach_ros.MonitorState('Robot/face',
                           	                      Int32MultiArray,
                           	                      monitor_FACE_MONITOR_cb,
                           	                      output_keys=['FACE_MONITOR_output']),
                           transitions={'valid':'FACE_PROCESSOR',
                                        'invalid':'FACE_PROCESSOR',
                                        'preempted':'FACE_TRACKER_exit'},
                           remapping={'FACE_MONITOR_output':'FACE_data'})
    smach.StateMachine.add('FACE_PROCESSOR',
                           FACE_PROCESSOR_state(),
                           transitions={'continue':'FACE_TRACKER_continue',
                                        'preempted':'FACE_TRACKER_exit'},
                           remapping={'FACE_PROCESSOR_input':'FACE_data',
                                      'FACE_PROCESSOR_output':'FACE_TRACKER_MODULE_output'})