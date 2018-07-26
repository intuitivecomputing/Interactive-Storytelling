import os
import json
from watson_developer_cloud import TextToSpeechV1
f = open("sysSpeech.json")
text = json.loads(f.read())["speech_sys"]
f.close()

audioPath = "./sysSpeechAudio/"

for key, value in text.iteritems():
	print value
	text_to_speech = TextToSpeechV1(
	    username='a43605e0-d9b4-402d-b3f2-ca0f56ba0a51',
	    password='0vqj1lPV1QeA')
	with open(audioPath + key + ".wav", 'wb') as audio_file:
	    audio_file.write(
	        text_to_speech.synthesize(
	            value, 'audio/wav', 'en-US_AllisonVoice').content)	