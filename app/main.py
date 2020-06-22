import json
from flask import Flask
from decouple import config
import requests
API_KEY = config('GOOGLE_STT_API_KEY')

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'Welcome to Lua Lep API!'

@app.route('/api/sentence/<file_name>', methods=['POST'])
def callSpeechToTextAPI(file_name):
    headers = {
        'Content-type': 'application/json',
    }
    data = {
        "config": {
            "encoding": "LINEAR16",
            "languageCode": "vi-VN",
            "sampleRateHertz": 44100
        },
        "audio": {
            "uri": "gs://lua-lep-app.appspot.com/recordings/"+file_name
        }
    }
    response = requests.post('https://speech.googleapis.com/v1/speech:recognize?key='+API_KEY, headers=headers, data=json.dumps(data))
    return response.content, headers
