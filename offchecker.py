import firebase_admin
from firebase_admin import db, credentials
import subprocess
import time


time.sleep(30)

cred = credentials.Certificate("/home/pi/Desktop/camera-service/key.json")
firebase_admin.initialize_app(cred, {"storageBucket": "safespace-1bdad.appspot.com", "databaseURL": "https://safespace-1bdad.firebaseio.com"})
    
user_id = 'w9X3C5bnoXPHd4dcplSAnVwsYNs1'
    

prev = 'false'

while True:
	ref = db.reference("users/{}/state/state".format(user_id)).get()
	print ref
	while ref == 'on':
		if prev == 'false':
			subprocess.Popen(['python','/home/pi/Desktop/camera-service/picamera-motion.py','&'])
			subprocess.Popen(['python','/home/pi/Desktop/camera-service/indoor-air-quality.py','&'])
			prev = 'true'
		time.sleep(1)
		ref = db.reference("users/{}/state/state".format(user_id)).get()
		if ref != 'on':
			subprocess.call(['pkill','-f','picamera-motion.py'])
			subprocess.call(['pkill','-f','indoor-air-quality.py'])
	prev = 'false'
	if ref == 'off':
		time.sleep(1)
	while ref == 'streaming':
		if prev == 'false':
			subprocess.Popen(['gunicorn','--threads','5','--workers','1','--bind','0.0.0.0:5000','--chdir', '/home/pi/Desktop/camera-service/flask-video-streaming', 'app:app','&'])
			prev = 'true'
		time.sleep(1)
		ref = db.reference("users/{}/state/state".format(user_id)).get()
		if ref != 'streaming':
			subprocess.call(['pkill', '-9','-f','flask-video-streaming'])
	prev = 'false'
