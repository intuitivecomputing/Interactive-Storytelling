import os
import json
import argparse
from watson_developer_cloud import TextToSpeechV1

'''
parser = argparse.ArgumentParser()
parser.add_argument("usr")
args = parser.parse_args()
print args.usr
'''
usrName = "Jee"
audioDic = {
    "audio1": "Hello, " + usrName,
    "audio6": usrName + ", it is your turn to go. Spin the wheel and wish for good luck.",
    "audio15": "Okay Maki, you will have to give up a card. Choose one and show it to " + usrName,
    "audio16": "Maki, you can have an extra card! Draw one extra card and show it to " + usrName,
    "audio19" : "Maki, you can use one of your card to challenge " + usrName,
    "audio20": usrName + ", you can use one of your card to challenge Maki. Choose one and show it to Maki.",
    "audio28": "Maki, you run out of cards so you cannot challenge " + usrName + " with an extra object. " + usrName + ", you are very lucky. You do not need to include any extra object in your story.",
    "audio29": usrName + ", you run out of cards so you cannot challenge Maki with an extra object. Maki, you are very lucky. You do not need to include any extra object in your story.",
    "audio31": "Moe gets home before Mew." + usrName + ", you win the game. Congratulations.",
    "audio35": usrName + ", you will be playing Moe and tries to get home no matter what happens. The game will start with you.",
    "audio37": "Maki, you first. Draw three cards and show them to " + usrName + ". Crayon, kite and rose.",
    "audio38": usrName + ", your turn to draw cards. Draw three cards from the stack and show them to Maki one by one."
}

text_to_speech = TextToSpeechV1(
  username='8ef4ef74-bc47-4412-81c3-f2550b9635ef',
  password='njL8tkHvaGKq')

audioPath = "../sysAudio/"

for key, value in audioDic.iteritems():
	with open(audioPath + key + ".wav", 'wb') as audio_file:
	    audio_file.write(
	        text_to_speech.synthesize(
	            value, 'audio/wav', 'en-US_AllisonVoice').content)

