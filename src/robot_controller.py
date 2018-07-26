#!/usr/bin/env python

import rospy
rospy.init_node('smach_example_state_machine', anonymous=True)
import smach
import smach_ros
from std_msgs.msg import String
from arbotix_msgs.msg import *
import arbotix_msgs.msg
from actionlib import *
from actionlib_msgs.msg import *
from arbotix_msgs.srv import SetSpeed
from arbotix_python.joints import *
from arbotix_python.servo_controller import *
from sensor_msgs.msg import JointState
import time
from sound_play.msg import SoundRequest, SoundRequestAction, SoundRequestGoal
import face_tracking_module
import json
from watson_developer_cloud import TextToSpeechV1
import roslib; roslib.load_manifest('sound_play')
import os


# may change, log in to ibm cloud to get a new one
'''
text_to_speech = TextToSpeechV1(
    username='a43605e0-d9b4-402d-b3f2-ca0f56ba0a51',
    password='0vqj1lPV1QeA')
'''


class Server:
    def __init__(self,name,i):
        pubs = ['/servo1_joint/command','/servo2_joint/command','/servo3_joint/command','/servo4_joint/command','/servo5_joint/command','/servo6_joint/command']
        self.joints = ['servo1_joint','servo2_joint','servo3_joint','servo4_joint','servo5_joint','servo6_joint']
        self.services = ['/servo1_joint/set_speed','/servo2_joint/set_speed','/servo3_joint/set_speed','/servo4_joint/set_speed','/servo5_joint/set_speed','/servo6_joint/set_speed']
        default_speed = [0.6, 0.6, 0.3, 0.3, 0.5, 1.0]
        

        self.stop = False
        self._sas = SimpleActionServer(name,
                ControlAction,
                execute_cb=self.execute_cb)
        self.pub = rospy.Publisher(pubs[i], Float64, queue_size=10)
        self.pose = 0.0
        self.sub = rospy.Subscriber('/joint_states', JointState, self.stateCb)
        self.i = i
        self.default_speed = default_speed[i]
        
    def stateCb(self, msg):
        idx = msg.name.index(self.joints[self.i])
        self.pose = msg.position[idx]


    def SetSpeed_client(self, speed):
         servo = self.services[self.i]
         rospy.wait_for_service(servo)
         
         try:
             set_speed = rospy.ServiceProxy(servo,SetSpeed)
             s = set_speed(speed)
             return s
         except rospy.ServiceException, e:
             print ("Service call failed") 


    def execute_cb(self, msg):

        targets = list(msg.target)
        
        if len(targets) == 0:
            self._sas.set_succeeded()
        else:
            for t in targets:              
                if t is None:
                    rospy.sleep(2.0)
                else:
                    self.SetSpeed_client(self.default_speed)
                    
                    if abs(t - self.pose) > self.default_speed:
                        speed = (abs(self.pose - t) - 0.5 * self.default_speed)
                    else:
                        speed = self.default_speed
                        
                    self.pub.publish(t)
                    
                    if self._sas.is_preempt_requested():
                        self._sas.set_preempted()
                        self.stop = True
                        break
                        
                    while not rospy.is_shutdown():
                        
                        if abs(self.pose - t) > 0.1:
                            self.SetSpeed_client(speed)
                        else:
                            self.SetSpeed_client(self.default_speed)
                            
                        self.pub.publish(t)
                        
                        if abs(t - self.pose) < 0.05:
                            break
            if not self.stop:
                self._sas.set_succeeded()
            else:
                self.stop = False

server1 = Server('CONTROLLER_servo1',0)
server2 = Server('CONTROLLER_servo2',1)
server5 = Server('CONTROLLER_servo5',4)
server6 = Server('CONTROLLER_servo6',5)

sm_ROBOT_CONTROL = smach.StateMachine(outcomes=['exit'])
sm_ROBOT_CONTROL.userdata.servo = [list(),list(),list(),list(),list(),list()]
sm_ROBOT_CONTROL.userdata.speech = ''
sm_ROBOT_CONTROL.face = False
sm_ROBOT_CONTROL.data = [0.0, 0.0]

with sm_ROBOT_CONTROL:

    def monitor_command_cb(ud, msg):
        print msg.speech
        ud.monitor_servo_output = []
        for each_list in msg.servo:
            ud.monitor_servo_output.append(each_list.element)
        ud.monitor_speech_output = msg.speech
        ud.monitor_face_output = msg.face

    smach.StateMachine.add('MONITOR',
                           smach_ros.MonitorState('command',
                                                  arbotix_msgs.msg.RobotCommand,
                                                  monitor_command_cb,
                                                  input_keys=['monitor_servo_output','monitor_speech_output','monitor_face_output'],
                                                  output_keys=['monitor_servo_output','monitor_speech_output','monitor_face_output']),
                           transitions={'invalid':'FACE_TRACKER_MODULE',
                                        'valid':'MONITOR',
                                        'preempted':'exit'},
                           remapping={'monitor_servo_output':'servo',
                                      'monitor_speech_output':'speech',
                                      'monitor_face_output':'face'})
    smach.StateMachine.add('FACE_TRACKER_MODULE',
                           face_tracking_module.sm_FACE_TRACKER,
                           transitions={'FACE_TRACKER_continue':'FACE_TRACKER',
                                        'FACE_TRACKER_exit':'exit'},
                           remapping={'FACE_TRACKER_MODULE_output':'data'})

    class FACE_TRACKER_state(smach.State):
        def __init__(self):
            smach.State.__init__(self, 
                                 outcomes=['preempted','continue'],
                                 input_keys=['FACE_TRACKER_servo_input','FACE_TRACKER_face_input','FACE_TRACKER_data_input','FACE_TRACKER_output'],
                                 output_keys=['FACE_TRACKER_output']) 

        def execute(self, userdata):
            if self.preempt_requested():
                self.service_preempt()
                return 'preempted'

            for i in range(6):
                userdata.FACE_TRACKER_output[i] = list(userdata.FACE_TRACKER_servo_input[i])

            if userdata.FACE_TRACKER_face_input:
                userdata.FACE_TRACKER_output[4].append(userdata.FACE_TRACKER_data_input[0])
                userdata.FACE_TRACKER_output[5].append(userdata.FACE_TRACKER_data_input[1])
            return 'continue'


    smach.StateMachine.add('FACE_TRACKER',
                           FACE_TRACKER_state(),
                           transitions={'continue':'CONTROLLER',
                                        'preempted':'exit'},
                           remapping={'FACE_TRACKER_output':'servo',
                                      'FACE_TRACKER_servo_input':'servo',
                                      'FACE_TRACKER_face_input':'face',
                                      'FACE_TRACKER_data_input':'data'})

      
    sm_CONTROL = smach.Concurrence(outcomes=['succeeded','aborted','preempted'],
                                   default_outcome='succeeded',
                                   input_keys = ['CONTROLLER_SERVO_input','CONTROLLER_SPEECH_input'])

    with sm_CONTROL:

        def goal_CONTROLLER_SERVO1_callback(userdata,default_goal):
            goal = ControlGoal()        
            goal.target = userdata.CONTROLLER_SERVO1_input[0]
            return goal

        def goal_CONTROLLER_SERVO2_callback(userdata,default_goal):
            goal = ControlGoal()        
            goal.target = userdata.CONTROLLER_SERVO2_input[1]
            return goal

        def goal_CONTROLLER_SERVO5_callback(userdata,default_goal):
            goal = ControlGoal()        
            goal.target = userdata.CONTROLLER_SERVO5_input[4]
            return goal
        
        def goal_CONTROLLER_SERVO6_callback(userdata,default_goal):
            goal = ControlGoal()        
            goal.target = userdata.CONTROLLER_SERVO6_input[5]
            return goal
        
        # SPEAKER
        # userdata.CONTROLLER_SPEAKER_input is the file name in storyAudio folder
        def goal_CONTROLLER_SPEAKER_callback(userdata,default_goal):
            #print "in robot speaker" 
            goal = SoundRequestGoal()
            soundPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/storyAudio/"
            if len(userdata.CONTROLLER_SPEAKER_input) == 0:
                #print "userdata len = 0"
                volume = 0.0
                soundPath = ""
            else:
                soundPath = soundPath + userdata.CONTROLLER_SPEAKER_input + ".wav"
                volume = 1.0
            '''
            with open(soundPath, 'wb') as audio_file:
                audio_file.write(text_to_speech.synthesize(
                    speech, 'audio/wav', 'en-US_MichaelVoice').content)
            '''
            print soundPath
            goal.sound_request.arg = soundPath
            goal.sound_request.sound = SoundRequest.PLAY_FILE
            goal.sound_request.command = SoundRequest.PLAY_ONCE
            goal.sound_request.volume = volume
            return goal
        
        smach.Concurrence.add('CONTROLLER_SERVO1',
                              smach_ros.SimpleActionState('CONTROLLER_servo1', ControlAction,
                                                          goal_cb = goal_CONTROLLER_SERVO1_callback,
                                                          input_keys = ['CONTROLLER_SERVO1_input']),
                              remapping={'CONTROLLER_SERVO1_input':'CONTROLLER_SERVO_input'})
                     
        smach.Concurrence.add('CONTROLLER_SERVO2',
                              smach_ros.SimpleActionState('CONTROLLER_servo2', ControlAction,
                                                          goal_cb = goal_CONTROLLER_SERVO2_callback,
                                                          input_keys = ['CONTROLLER_SERVO2_input']),
                              remapping={'CONTROLLER_SERVO2_input':'CONTROLLER_SERVO_input'})
        
        smach.Concurrence.add('CONTROLLER_SERVO5',
                              smach_ros.SimpleActionState('CONTROLLER_servo5', ControlAction,
                                                          goal_cb = goal_CONTROLLER_SERVO5_callback,
                                                          input_keys = ['CONTROLLER_SERVO5_input']),
                              remapping={'CONTROLLER_SERVO5_input':'CONTROLLER_SERVO_input'})

        smach.Concurrence.add('CONTROLLER_SERVO6',
                              smach_ros.SimpleActionState('CONTROLLER_servo6', ControlAction,
                                                          goal_cb = goal_CONTROLLER_SERVO6_callback,
                                                          input_keys = ['CONTROLLER_SERVO6_input']),
                              remapping={'CONTROLLER_SERVO6_input':'CONTROLLER_SERVO_input'})

        smach.Concurrence.add('CONTROLLER_SPEAKER',
                              smach_ros.SimpleActionState('storysound_play', SoundRequestAction,
                                                          goal_cb = goal_CONTROLLER_SPEAKER_callback,
                                                          input_keys = ['CONTROLLER_SPEAKER_input']),
                              remapping={'CONTROLLER_SPEAKER_input':'CONTROLLER_SPEECH_input'})    

    smach.StateMachine.add('CONTROLLER',
                           sm_CONTROL,
                           transitions={'succeeded':'DONE',
                                        'aborted':'exit',
                                        'preempted':'exit'},
                           remapping={'CONTROLLER_SERVO_input':'servo',
                                      'CONTROLLER_SPEECH_input':'speech'})

    class DONE_state(smach.State):
        def __init__(self):
            smach.State.__init__(self, 
                                 outcomes=['preempted','continue'])
            #self.pub = rospy.Publisher('ROBOT/done', String, queue_size=10) 

        def execute(self, userdata):
            if self.preempt_requested():
                self.service_preempt()
                return 'preempted'
            pub = rospy.Publisher('ROBOT/done', String, queue_size=10)
            rospy.sleep(1.0)
            msg = String()
            msg.data = '1'
            pub.publish(msg)
            rospy.sleep(0.2)
            return 'continue'

    smach.StateMachine.add('DONE',
                           DONE_state(),
                           transitions={'continue':'MONITOR',
                                        'preempted':'exit'})

    sis = smach_ros.IntrospectionServer('server_name', sm_ROBOT_CONTROL, '/ROOT')
    sis.start()
    outcome = sm_ROBOT_CONTROL.execute()
    rospy.spin()
    sis.stop()


if __name__ == '__main__':
    main()