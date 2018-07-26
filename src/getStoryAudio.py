import os
import json
from watson_developer_cloud import TextToSpeechV1

audioPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/sysAudio/"

f = open(os.path.dirname(os.path.abspath(__file__)) + "/sysSetting.json")
text = json.loads(f.read())["setting_sys"]
f.close()

for dics in text:
	key, value = dics["name"], dics["story"]
	text_to_speech = TextToSpeechV1(
	    username='a43605e0-d9b4-402d-b3f2-ca0f56ba0a51',
	    password='0vqj1lPV1QeA')
	with open(audioPath + key + ".wav", 'wb') as audio_file:
	    audio_file.write(
	        text_to_speech.synthesize(
	            value, 'audio/wav', 'en-US_AllisonVoice').content)
