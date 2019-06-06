#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response
import socket

# import camera driver
Camera = import_module('camera_pi').Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

import firebase_admin
from firebase_admin import credentials, firestore, storage, db
cred = credentials.Certificate("/home/pi/Desktop/camera-service/key.json")
firebase_admin.initialize_app(cred, {"storageBucket": "safespace-1bdad.appspot.com", "databaseURL": "https://safespace-1bdad.firebaseio.com"})

def get_ip(user_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255',1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
    
def get_user_id(device_id):
    
    return db.reference("devices/{}/users".format(device_id)).get().values()[0].encode('ascii','ignore')


user_id = get_user_id("pi1")
stream_url = 'http://' + get_ip(user_id) + ':5000/video_feed'
db.reference("users/{}/streamUrl".format(user_id)).set(stream_url)

app = Flask(__name__)


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    

    app.run(host='0.0.0.0', threaded=True)
    
