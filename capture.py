import schedule
import time
from datetime import datetime, timezone, time, timedelta
import pymongo
import os
import uuid
from typing import List
import cv2
import detectapi
from pydantic import BaseModel

mongocreds = os.getenv("mongocred")
base = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
db=base["tablesense"]

client = "acme"
scheduleraw = db[f"{client}-schedule"].find()

def controlcapture(room:str, sector:int, id:str, days:List[str]):
    
    if datetime.now().strftime("%A") in days:
        # try:
        cap = cv2.VideoCapture(detectapi.getCamLink(client,room,sector)["link"]) #IP Camera
        ret, frame = cap.read()
        frame = cv2.resize(frame,(1024, 576))
        cv2.imwrite(f"imagedata/control/{room}-{id}-{sector}.png", frame)
        print(f"Captured control at room {room}, image ID: {room}-{id}-{sector}")
        # except Exception as e:
        #     print(str(e.with_traceback))

def currentcapture(room:str, sector:int, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        # try:
        cap = cv2.VideoCapture(detectapi.getCamLink(client,room,sector)["link"]) #IP Camera
        ret, frame = cap.read()
        frame = cv2.resize(frame,(1024, 576))
        cv2.imwrite(f"imagedata/captures/{room}-{id}-{sector}.png", frame)
        print(f"Captured current at room {room}, image ID: {room}-{id}-{sector}")
        # except Exception as e:
        #     print(str(e.with_traceback))


from detectapi import Detect

def sendhighlightcall(control,current, sectors, client, room, days):
    
    if datetime.now().strftime("%A") in days:
        print(detectapi.detectstain(detect= detectapi.Detect(
                                    control = control,
                                    current = current,
                                    sectors = sectors,
                                    client = client,
                                    room = room,
                                    crop = True,
                                    color = "blue",
                                    shape = "auto",
                                    format="png"
                                )
                            )
                        )

for i in scheduleraw:
    controlID = str(uuid.uuid4())
    for sector in i["sectors"]:
        schedule.every().day.at(time.fromisoformat(i["start"]).strftime("%H:%M")).do(controlcapture,room=i["room"], sector = sector, id= controlID, days = i["days"] )
    currentID = str(uuid.uuid4())
    for sector in i["sectors"]:
        schedule.every().day.at(time.fromisoformat(i["end"]).strftime("%H:%M")).do(currentcapture,room=i["room"], sector = sector, id= currentID, days = i["days"] )
    # Convert to datetime (using a dummy date)
    detectdatetime = datetime.combine(datetime.min.date(), time.fromisoformat(i["end"]))
    # Add 5 seconds
    detecttime = detectdatetime + timedelta(seconds=5)
    schedule.every().day.at(detecttime.time().strftime("%H:%M")).do(sendhighlightcall, control = f"{i["room"]}-{controlID}",current = f"{i["room"]}-{currentID}", sectors= i["sectors"], client = client, room = i["room"], days = i["days"])

    # controlID = str(uuid.uuid4())
    # for sector in i["sectors"]:
    #     controlcapture(room=i["room"], sector = sector, id= controlID, days = i["days"] )
    # currentID = str(uuid.uuid4())
    # for sector in i["sectors"]:
    #     currentcapture(room=i["room"], sector = sector, id= currentID, days = i["days"] )
    # # Convert to datetime (using a dummy date)
    # detectdatetime = datetime.combine(datetime.min.date(), time.fromisoformat(i["end"]))
    # # Add 5 seconds
    # detecttime = detectdatetime + timedelta(seconds=5)
    # sendhighlightcall(control = f"{i["room"]}-{controlID}",current = f"{i["room"]}-{currentID}", sectors= i["sectors"], client = client, room = i["room"], days = i["days"])

while True:
    schedule.run_pending()