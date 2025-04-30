import schedule
import time
from datetime import datetime, timezone, time, timedelta
import pymongo
import os
import uuid
from typing import List
import cv2
import detectapi


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
            cv2.imwrite(f"imagedata/control/{room}-{id}-1.png", frame)
            print(f"Captured control at room {room}, image ID: {room}-{id}-1")
        except Exception as e:
            print(e.with_traceback)
def currentcapture(room:str, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        try:
            cap = cv2.VideoCapture(os.getenv("camlink")) #IP Camera
            ret, frame = cap.read()
            frame = cv2.resize(frame,(1024, 576))
            cv2.imwrite(f"imagedata/captures/{room}-{id}-1.png", frame)
            print(f"Captured current at room {room}, image ID: {room}-{id}-1")
        except Exception as e:
            print(e.with_traceback)

def sendhighlightcall(control,current, sector_num, client, room):
    print(detectapi.detectstain(control,current, sector_num, client, room, crop = True, crop_color = "blue", crop_shape= "auto", format="png"))

for i in scheduleraw:
    controlID = str(uuid.uuid4())
    schedule.every().day.at(time.fromisoformat(i["start"]).strftime("%H:%M")).do(controlcapture,room=i["room"], id= controlID, days = i["days"] )
    currentID = str(uuid.uuid4())
    schedule.every().day.at(time.fromisoformat(i["end"]).strftime("%H:%M")).do(currentcapture,room=i["room"], id= currentID, days = i["days"] )
    # Convert to datetime (using a dummy date)
    detectdatetime = datetime.combine(datetime.min.date(), time.fromisoformat(i["end"]))
    # Add 5 seconds
    detecttime = detectdatetime + timedelta(seconds=5)
    schedule.every().day.at(detecttime.time().strftime("%H:%M")).do(sendhighlightcall, control = f"{i["room"]}-{controlID}",current = f"{i["room"]}-{currentID}", sector_num= 1, client = client, room = i["room"] )

while True:
    schedule.run_pending()