import schedule
import time
from datetime import datetime, timezone, time
import pymongo
import os
import uuid
from typing import List
import cv2

mongocreds = os.getenv("mongocred")
base = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
db=base["tablesense"]

client = "testclient"
scheduleraw = db[f"{client}-schedule"].find()

def controlcapture(room:str, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        try:
            cap = cv2.VideoCapture(os.getenv("camlink")) #IP Camera
            ret, frame = cap.read()
            frame = cv2.resize(frame,(1024, 576))
            cv2.imwrite(f"imagedata/control/{room}-{id}.png", frame)
            print(f"Captured control at room {room}, image ID: {room}-{id}")
        except Exception as e:
            print(e.with_traceback())
def currentcapture(room:str, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        try:
            cap = cv2.VideoCapture(os.getenv("camlink")) #IP Camera
            ret, frame = cap.read()
            frame = cv2.resize(frame,(1024, 576))
            cv2.imwrite(f"imagedata/captures/{room}-{id}.png", frame)
            print(f"Captured current at room {room}, image ID: {room}-{id}")
        except Exception as e:
            print(e.with_traceback())

for i in scheduleraw:
    schedule.every().day.at(time.fromisoformat(i["start"]).strftime("%H:%M")).do(controlcapture,room=i["room"], id= str(uuid.uuid4()), days = i["days"] )
    schedule.every().day.at(time.fromisoformat(i["end"]).strftime("%H:%M")).do(currentcapture,room=i["room"], id= str(uuid.uuid4()), days = i["days"] )


while True:
    schedule.run_pending()
    