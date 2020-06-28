import json
from flask import Flask, request
import decouple
import requests

API_KEY = "AIzaSyDU1UwxBepNeDCEeydO7D0BdXLMMUptCdQ"

app = Flask(__name__)

def check(words_recognize, words):
    for i, word in enumerate(words):
        word_recognize = words_recognize[i]
        if(word[0] != 'l' and word[0] != 'n'):
            continue
        if(word_recognize[0] != word[0] and word_recognize[1] != word[0] and word_recognize[2] != word[0]):
            return False
    return True

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
            "languageCode": "en-US",
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
        word_recognize_split = str(word_recognize).split();
        word_split = word.split();
        if check(word_recognize_split, word_split) == False:
            passed = False
        #if str(word_recognize) != word or confidence < 0.7:
        #    passed = False
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
