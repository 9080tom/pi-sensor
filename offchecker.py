import firebase_admin
from firebase_admin import db, credentials
import subprocess
import time

cred = credentials.Certificate("/home/pi/Desktop/camera-service/key.json")
firebase_admin.initialize_app(cred, {"storageBucket": "safespace-1bdad.appspot.com", "databaseURL": "https://safespace-1bdad.firebaseio.com"})
    
user_id = 'w9X3C5bnoXPHd4dcplSAnVwsYNs1'
    

prev = 'off'

while True:
	ref = db.reference("users/{}/state".format(user_id)).get()
	print ref
	while ref == 'on':
		if prev == 'off':
			subprocess.Popen(['python','picamera-motion.py','&'])
			subprocess.Popen(['python','indoor-air-quality.py','&'])
			prev = 'true'
		time.sleep(300)
		ref = db.reference("users/{}/state".format(user_id)).get()
		if ref == 'off':
			subprocess.call(['pkill','-f','picamera-motion.py'])
			subprocess.call(['pkill','-f','indoor-air-quality.py'])
	if ref == 'off':
		time.sleep(300)
		
