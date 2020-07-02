import json
from flask import Flask, request, send_from_directory
import decouple
import requests
from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
import speech_recognition as sr
import pyrebase

API_KEY = "AIzaSyDU1UwxBepNeDCEeydO7D0BdXLMMUptCdQ"

app = Flask(__name__)

def upload(file_local, file_on_cloud):
    config = {
        "apiKey": "AIzaSyDF7_dLIcMTSfZBEcFEp92Hokf45cANGJo",
        "authDomain": "lua-lep-app.firebaseapp.com",
        "databaseURL": "https://lua-lep-app.firebaseio.com",
        "projectId": "lua-lep-app",
        "storageBucket": "lua-lep-app.appspot.com",
        "messagingSenderId": "1088593378829",
        "appId": "1:1088593378829:web:4e5e1f6a7a97db5545df44",
        "measurementId": "G-BRBPH3BVBF"
        }
    firebase = pyrebase.initialize_app(config)
    storage = firebase.storage()

    path_on_cloud = "recordings/" + file_on_cloud
    path_local = file_local
    storage.child(path_on_cloud).put(path_local)


def check(words_recognize, words):
    passed = True
    for i, word in enumerate(words):
        word_recognize = words_recognize[i]
        if(word[0].lower() != 'l' and word[0].lower() != 'n'):
            #print("exit 1")
            continue
        if(word[0].lower() == 'n'):
            if(word[1].lower() == 'g' or word[1].lower() == 'h'):
                #print("exit 2")
                continue
        if(word_recognize[0].lower() != word[0].lower() and word_recognize[1].lower() != word[0].lower()):
            passed = False
    return passed

def recognizer(audio_file, word):
    passed = True
    message = ""
    headers = {
        'Content-type': 'application/json',
    }
    data = {
        "config": {
            "encoding": "LINEAR16",
            "languageCode": "en-US",
            "sampleRateHertz": 44100,
            "model": "video"
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
        if (check(word_recognize_split, word_split) == False):
            passed = False
    except:
        passed = False
    return passed

@app.route('/')
def welcome():
    return 'Welcome to Lua Lep API!'


@app.route('/api/sentence', methods=['POST'])
def callSpeechToTextAPI():
    passed = True
    message = ""
    word = request.args.get('word', None)
    #print(word)
    word_split = word.split();
    audio_file = request.args.get('audio_file', None)
    url = 'https://firebasestorage.googleapis.com/v0/b/lua-lep-app.appspot.com/o/recordings%2F' + audio_file+ '?alt=media'
    r = requests.get(url)
    
    with open('./data.wav', 'wb') as f:
        f.write(r.content)
    sound_file = AudioSegment.from_wav("data.wav")

    if not os.path.exists('./splitAudio'):
        os.makedirs('./splitAudio')
    
    audio_chunks = split_on_silence(sound_file, 
        # must be silent for at least 70ms
        min_silence_len=70,

        # consider it silent if quieter than -25 dBFS
        silence_thresh=-25
    )
    accuracy = "Chúc mừng bạn"
    message = "Bạn đã đọc đúng ✅"
    passed = True
    if(len(audio_chunks) != len(word_split)):
        passed = False
        message = "Mời bạn đọc lại ❗️"
        accuracy = "Bạn đã đọc quá nhanh"
        
        response = {
            "passed": passed,
            "accuracy": accuracy,
            "message": message
        }
        return response
    words = []
    for i, chunk in enumerate(audio_chunks):
        word_passed = True
        out_file = "./splitAudio/chunk{0}.wav".format(i)
        ##print("exporting", out_file)
        chunk.export(out_file, format="wav")
        upload("./splitAudio/chunk{0}.wav".format(i), "chunk{0}.wav".format(i))
        if(recognizer("chunk{0}.wav".format(i), word_split[i]) == False):
            word_passed = False
            passed = False
            message = "Mời bạn đọc lại ❗️"
            accuracy = "Có vẻ như bạn bị ngọng"
        this = {"word": word_split[i],
                "passed": word_passed
                }
        words.append(this)
    response = {
            "passed": passed,
            "accuracy": accuracy,
            "message": message,
            "words": words
        }
    return response



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
            "sampleRateHertz": 44100,
            "model": "video"
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
        #print(response)
        #print(word_recognize)
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
