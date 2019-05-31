import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {"storageBucket": "safespace-1bdad.appspot.com"})
db = firestore.client()
bucket = storage.bucket()
blob = bucket.blob("w9X3C5bnoXPHd4dcplSAnVwsYNs1/hello2.txt")
outfile = "hello.txt"
with open(outfile, "rb") as my_file:
    blob.upload_from_file(my_file)
