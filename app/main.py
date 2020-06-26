import json
from flask import Flask, request
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
            "uri": "gs://lua-lep-app.appspot.com/recordings/" + file_name
        }
    }
    response = requests.post('https://speech.googleapis.com/v1/speech:recognize?key=' + API_KEY, headers=headers,
                             data=json.dumps(data))
    return response.content, headers


@app.route('/api/word', methods=['POST'])
def checkWord():
    passed = True
    message = ""
    word = request.args.get('word', None)
    audio_file = request.args.get('audio_file', None)
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
            "uri": "gs://lua-lep-app.appspot.com/recordings/" + audio_file
        }
    }
    response = requests.post('https://speech.googleapis.com/v1/speech:recognize?key=' + API_KEY, headers=headers,
                             data=json.dumps(data))
    confidence = 0.0
    accuracy = ''
    try:
        word_recognize = response.json().get('results')[0].get('alternatives')[0].get('transcript')
        confidence = response.json().get('results')[0].get('alternatives')[0].get('confidence')
        if str(word_recognize) != word or confidence < 0.7:
            passed = False
    except:
        passed = False
    if passed:
        accuracy = "Độ chính xác "+"{:.2f}".format(confidence * 100) + "%"
        message = "Bạn đã đọc đúng ✅"
    else:
        accuracy = "Có vẻ như bạn bị ngọng"
        message = "Mời bạn đọc lại ❗️"

    return {
        "word": word,
        "accuracy": accuracy,
        "passed": passed,
        "message": message
    }
