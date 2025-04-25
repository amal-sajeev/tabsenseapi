from fastapi import FastAPI, Body, HTTPException, File, UploadFile,status
import staindet
from typing import Union, Annotated, List
from PIL import Image
import pymongo, json, uuid
from datetime import datetime, timezone
import os

app = FastAPI()

mongocreds = os.getenv("mongocred")
client = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
db=client["tablesense"]

@app.get("/detect")
def detectstain(control, current, sector_num:int, client, room, crop:bool=True, crop_color = "blue", crop_shape= "auto", format:str="png"):
    """Endpoint that reads a control image, the current image, and by comparing the two detects whether there's a stain on the current surface. If the tables aren't captured properly, as long as there's a coloured border on the surfaces, the crop parameter can be used to isolate the surface.

    Args:
    
        control (string): UUID of control images from all sectors, which is the clean surface under the current conditions.
        
        current (string): UUID of current images from all sectors, the most recent image of the surface.
        
        sector_num (int): Number of sectors in the room.
        
        room (string): The room where the alerts should be sent and the detected images should be stored. Used for mongo collection.
        
        crop (bool, optional): Whether to isolate the surface based on a coloured border. Defaults to True.
        
        color (str, optional): The colour of the border. Allowed colour ranges are blue, red, green, yellow. Defaults to "blue".
        
        shape (str, optional): The shape of the table and the border. Allowed options are 'auto', 'rectangle', 'circle', and 'oval'. Auto can automatically detect the shape and is most recommended. Defaults to "auto".
        
        format (str, optional): The filetype of the image. Defaults to "png".
    """
    #Only for use after module works with pil image inputs.
    # if type(control) == str:
    #     control = staindet._open_image(control)
    # if type(current) == str:
    #     current = staindet._open_image(current)

    try:
        current_results = {
            "id" : control.split("/")[-1].split(".")[0],
            "timestamp": datetime.now(timezone.utc),
            "detections" : 0,
            "sectors" : {}
        }
        
        for i in range(1,sector_num+1):
            print(i)
            detected = staindet.detect(
            control = f"imagedata/control/{control}-{i}.{format}",
            current = f"imagedata/captures/{current}-{i}.{format}",
            crop = crop,
            color = crop_color,
            shape = crop_shape,
            displayresults= False,
            savehighlight=f"Sector_{current_results['id']}-{i}_highlight")
            print(type(detected))
            if detected ==  "True":
                current_results["sectors"][str(i)] = {
                    "highlight": f"Sector_{current_results['id']}-{i}_highlight.png",
                    "control": f"{control}-{i}.{format}"
                }
        current_results["detections"] = len(current_results["sectors"].keys())
        db[f'{client}-{room}'].insert_one(current_results)

        return(current_results['sectors'])

    except Exception as e:
        return({"error": str(e.with_traceback())})


@app.post("/report")
def getreport(room, client, start: Annotated[datetime, Body()] = None, end: Annotated[datetime, Body()] = None):
    """
    Gets all data in a date range.

    Args:
        room (String) = Name of the room to get reports from.
        client (String) = Name of the client.
        start (String) = Date of beginning of date range. Optional.
        end (String) = Date of ending of date range. Optional.
    """
    try:
        # Build query based on provided para                                                                                                            meters
        query = {}
        if start is not None or end is not None:
            query["timestamp"] = {}
            if start is not None:
                query["timestamp"]["$gte"] = start
            if end is not None:
                query["timestamp"]["$lt"] = end
        
        # Execute query with or without timestamp filters
        return [i for i in db[f'{client}-{room}'].find(query, {"_id": False})]
    except Exception as e:
        return({"error": str(e.with_traceback())})

# SCHEDULE CRUD

@app.post("/addentry")
def addScheduleEntry(client:str, room:str, label:str, start:Annotated[datetime, Body()], end:Annotated[datetime, Body()]):
    """Add a time period in the schedule.

    Args:                
        client (str): The client that the room belongs to.
        room (str): The room name or ID to represent the room.
        label (str): Label for this entry.
        start (Annotated[datetime,body): The time at which the control image is taken, for clean surfaces.
        end (Annotated[datetime,body): The time at which the current image is captured, to compare with the control image and recognize stains.
    """
    try:
        entry = {
            "id": str(uuid.uuid4()),
            "label": label,
            "start": start,
            "end": end,
            "room": room
        }
        db[f'{client}-schedule'].insert_one(entry)
        return(f"Inserted into schedule for {room}")
    except Exception as e:
        return({"error": str(e.with_traceback())})


@app.post("/entry/add")
def addScheduleEntry(client:str, room:str, label:str, start:Annotated[datetime, Body()], end:Annotated[datetime, Body()]):
    """Add a time period in the schedule.

    Args:                aqe
        client (str): The client that the room belongs to.
        room (str): The room name or ID to represent the room.
        label (str): Label for this entry.
        start (Annotated[datetime,body): The time at which the control image is taken, for clean surfaces.
        end (Annotated[datetime,body): The time at which the current image is captured, to compare with the control image and recognize stains.
    """
    try:
        entry = {
            "id": str(uuid.uuid4()),
            "label": label,
            "start": start,
            "end": end,
            "room": room
        }
        db[f'{client}-schedule'].insert_one(entry)
        return(f"Inserted into schedule for {room}")
    except Exception as e:
        return({"error": str(e.with_traceback())})


@app.post("/entry/deleteone")
def deleteScheduleEntry(id:str):
    """Delete a time period in the schedule.

    Args:
        id (str): id of the time period entry.
    """
    try:
        db[f'{client}-schedule'].delete_one({"id":id})
    except Exception as e:
        return({"error": str(e.with_traceback())})

@app.post("/entry/delete")
def deleteScheduleEntries(client:str,id:List[str]):
    
    return(str(db[f'{client}-schedule'].delete_many({"id":{"$in":id}})))
