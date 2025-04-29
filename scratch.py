import schedule
import time
from datetime import datetime, timezone, time
import pymongo
import os
import uuid
from typing import List

def controlcapture(room:str, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        print(f"Captured control at room {room}, image ID: {id}")

def currentcapture(room:str, id:str, days:List[str]):
    if datetime.now().strftime("%A") in days:
        print(f"Captured current at room {room}, image ID: {id}")

print(datetime.now(timezone.utc).strftime("%A")=="Tuesday")

mongocreds = os.getenv("mongocred")
base = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
db=base["tablesense"]

client = "testclient"
scheduleraw = db[f"{client}-schedule"].find()

for i in scheduleraw:
    print(time.fromisoformat(i["start"]))
    print(i["start"])
    schedule.every().day.at(time.fromisoformat(i["start"]).strftime("%H:%M")).do(controlcapture,room=i["room"], id= str(uuid.uuid4()), days = i["days"] )
    schedule.every().day.at(time.fromisoformat(i["end"]).strftime("%H:%M")).do(currentcapture,room=i["room"], id= str(uuid.uuid4()), days = i["days"] )


while True:
    schedule.run_pending()