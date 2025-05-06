from fastapi import FastAPI, Body, HTTPException, File, UploadFile,status
from pydantic import BaseModel
import staindet
from typing import Union, Annotated, List, Optional
from PIL import Image
import pymongo, json, uuid
from datetime import datetime, timezone, time
import os

app = FastAPI()

mongocreds = os.getenv("mongocred")
client = pymongo.MongoClient(f"mongodb://{mongocreds}@localhost:27017")
db=client["tablesense"]

class Detect(BaseModel):
    control:str
    current:str
    sectors:List[int]
    client:str
    room:str
    crop:bool
    color:str
    shape:str
    format:str
    # def __init__(control:str,current:str,sectors:List[int],client:str,room:str,crop:bool = True,color:str = "blue",shape:str = "auto",format:str = "png"):
    #     return(Detect(
    #                     control,
    #                     current,
    #                     sectors,
    #                     client,
    #                     room,
    #                     crop,
    #                     color,
    #                     shape,
    #                     format
                    # ))
@app.get("/detect")
def detectstain(detect:Detect):
    """Endpoint that reads a control image, the current image, and by comparing the two detects whether there's a stain on the current surface. If the tables aren't captured properly, as long as there's a coloured border on the surfaces, the crop parameter can be used to isolate the surface.

    Args:
    
        {
            control (string): UUID of control images from all sectors, which is the clean surface under the current conditions.
            current (string): UUID of current images from all sectors, the most recent image of the surface.
            sectors (List[int]): List of sectors in the room.
            room (string): The room where the alerts should be sent and the detected images should be stored. Used for mongo collection.
            crop (bool, optional): Whether to isolate the surface based on a coloured border. Defaults to True.
            color (str, optional): The colour of the border. Allowed colour ranges are blue, red, green, yellow. Defaults to "blue".
            shape (str, optional): The shape of the table and the border. Allowed options are 'auto', 'rectangle', 'circle', and 'oval'. Auto can automatically detect the shape and is most recommended. Defaults to "auto".
            format (str, optional): The filetype of the image. Defaults to "png".
        }
    """
    #Only for use after module works with pil image inputs.
    # if type(control) == str:
    #     control = staindet._open_image(control)
    # if type(current) == str:
    #     current = staindet._open_image(current)

    # try:
    current_results = {
        "id" : detect.control.split("/")[-1].split(".")[0],
        "timestamp": datetime.now(timezone.utc),
        "detections" : 0,
        "sectors" : {}
    }
    
    for i in detect.sectors:
        print(i)
        detected = staindet.detect(
        control = f"imagedata/control/{detect.control}-{i}.{detect.format}",
        current = f"imagedata/captures/{detect.current}-{i}.{detect.format}",
        crop = detect.crop,
        color = detect.color,
        shape = detect.shape,
        displayresults= True,
        savehighlight=f"Sector_{current_results['id']}-{i}_highlight")
        print(type(detected))
        if detected ==  "True":
            current_results["sectors"][str(i)] = {
                "highlight": f"Sector_{current_results['id']}-{i}_highlight.png",
                "control": f"{detect.control}-{i}.{detect.format}"
            }
    current_results["detections"] = len(current_results["sectors"].keys())
    db[f'{detect.client}-{detect.room}'].insert_one(current_results)

    return(current_results['sectors'])

    # except Exception as e:
    #     return({"error": str(e.with_traceback)})


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
        return({"error": str(e.with_traceback)})

# SCHEDULE CRUD

class Entry(BaseModel):
    client: str = None
    id: str = None
    room: str = None
    label: str = None
    start: time = None
    end: time = None
    sectors : list = []
    days: List[str] = []

@app.post("/entry/add")
def addScheduleEntry(entry:Entry):
    """Add a time period in the schedule.

    Args:
        entry (Entry): Details of schedule entry to add, format:
            {
                "client" (str): The client that the room belongs to.        
                "room" (str): The room name     or ID to represent the room.
                "label" (str): Label for this entry.
                "start" (Annotated[time,body): The time at which the control image is taken, for clean surfaces.
                "end" (Annotated[time,body): The time at which the current image is captured, to compare with the control image and recognize stains.
                "sectors" (List[int]): A list of sectors to capture pictures from.
                "days" (List[str]): A list of days, in words and title case, where the capture should be triggered.
            }
    """
    try:
        dentry = {
            "id": str(uuid.uuid4()),
            "label": entry.label,
            "start": entry.start.isoformat(),
            "end": entry.end.isoformat(),
            "room": entry.room,
            "sectors" : entry.sectors,
            "days": entry.days
        }
        db[f'{entry.client}-schedule'].insert_one(dentry)
        return(f"Inserted into schedule for {entry.room}")
    except Exception as e:
        return({"error": str(e.with_traceback)})

@app.post("/entry/deleteone")
def deleteScheduleEntry(id:str, client:str, room:str):
    """Delete a time period in the schedule.

    Args:
        id (str): id of the time period entry.
        "client" (str): The client that the room belongs to.
    """
    try:
        db[f'{client}-schedule'].delete_one({"id":id})
    except Exception as e:
        return({"error": str(e.with_traceback)})

@app.post("/entry/delete") 
def deleteScheduleEntries(client:str,id:List[str]=[], room:str=""):
    """Delete multiple entries based on list of IDs or all entries related to a room.

    Args:
        client (str): The client that the room belongs to.
        id (List[str]): id of the time period entry.
        room(str): The room name or ID used to represent the room.
    """
    try:
        filterstring={}
        if id!=[]:
            filterstring["id"] = {"$in":id}
        if room !="":
            filterstring["room"] = room
        return(str(db[f'{client}-schedule'].delete_many(filterstring)))
    except Exception as e:
        return({"error": str(e.with_traceback)})


@app.get("/entry")
def getScheduleEntry(
    client: Optional[str] = None,
    id: Optional[str] = None,
    room: Optional[str] = None,
    label: Optional[str] = None,
    start: Optional[time] = None,
    end: Optional[time] = None
):
    """Get schedule entries, using id, room, label, and a date range to filter optionally.

    Args:
        client (str): The client that the room belongs to.
        room (str): The room name or ID to represent the room.
        label (str): Label for this entry.
        start (time): The time at which the control image is taken, for clean surfaces.
        end (time): The time at which the current image is captured, to compare with the control image and recognize stains.
    """

    # try: 
    filterstring = {}
    if client:
        # Make sure to use the client variable, not a non-existent entry object
        collection = f"{client}-schedule"
    else:
        raise HTTPException(status_code=400, detail="Client is required")
        
    if id:
        filterstring["id"] = id
    if room:
        filterstring["room"] = room
    if label:
        filterstring["label"] = label
    if start is not None:
        filterstring["start"] = {"$gte" : start.isoformat()}
    if end is not None: 
        filterstring["end"] = {"$lt": end.isoformat()}
            
    # Return the found documents, assuming db is properly defined elsewhere
    result = list(db[collection].find(filterstring, {"_id": False}))
    return result           
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/entry/update")
def updateScheduleEntry(client:str,id:str, entry:Entry):
    """Update a schedule entry based on the id.

    Args:
        id (str): ID of the schedule entry to be updated.
        entry (Entry): The entry details to update.
    """
    # try:
    uentry = {"$set":{}}
    if entry.room:
        uentry["$set"].update( {"room": entry.room})
    if entry.label:
        uentry["$set"].update( {"label": entry.label})
    if entry.start is not None:
        uentry["$set"].update({"start": entry.start.isoformat()})
    if entry.end is not None: 
        uentry["$set"].update({"end": entry.end.isoformat()})
    if entry.days is not None:
        uentry["$set"].update({"days": entry.days})

    return(str(db[f"{client}-schedule"].update_one({"id":id},uentry)))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

#Camera link CRUD

class CamLink(BaseModel):
    id:str = str(uuid.uuid4())
    client:str = ""
    room:str = ""
    sector:int= None
    link:str = ""

@app.post("/cam")
def addCamLink(camlink:CamLink):
    """Enter information for a camera in the database.

    Args:
        camlink (CamLink): Entry for camera database. ID is optional. Format:
                            {
                                id:str
                                client:str
                                room:str
                                sector:int
                                link:str
                            }
    """
    try:
        newcam = {
            "id" : camlink.id,
            "client" : camlink.client,
            "room" : camlink.room,
            "sector" : camlink.sector,
            "link" : camlink.link
        }
        db[f'{camlink.client}-cams'].insert_one(newcam)
        return(f"Inserted into camera database for sector {camlink.sector} in room {camlink.room}")   
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/cam")
def getCamLink(client:str, room: str="", sector:int =None, id:str = ""):
    
    try:
        if id != "":
            result = db[f"{client}-cams"].find_one({"id":id}, {"_id": False})
            if result == None:
                raise HTTPException(status_code=404, detail=f"Camera with id {id} not found!")
            return(result)
        elif room !="" and sector !=None:
            result = db[f"{client}-cams"].find_one({"room":room, "sector": sector }, {"_id": False})
            if result == None:
                raise HTTPException(status_code=404, detail=f"Camera at room {room}, sector {sector} not found!")
            return(result)
        else:
            raise HTTPException(status_code=500, detail=f"Either enter both sector and room, or ID.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
 
@app.post("/cam/delete")
def deleteCam(client:str, room: str="", sector:int =None, id:str = ""):

    try:
        if id != "":
            return(str(db[f"{client}-cams"].delete_one({"id":id})))
        elif room !="" and sector !="":
            return(str(db[f"{client}-cams"].delete_one({"room":room, "sector": sector })))
        elif room!="" and sector==None:
            return(str(db[f"{client}-cams"].delete_many({"room":room})))
        else:
            raise HTTPException(status_code=500, detail=f"Either enter both sector and room, or ID.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/cam/update")
def updateCam(client:str,id:str, camlink:CamLink):
    """Update a camera entry based on the id or room and sector.

    Args:
        id (str): ID of the schedule entry to be updated.e
        camlink (CamLink): The camera details to update. ID cannot be updated. Simply put any data you wish to update. Format:
                            {
                                room:str
                                sector:int
                                link:str
                            }
    """
    try:
        ucam = {"$set":{}}
        if camlink.room != "": 
            ucam["$set"].update( {"room": camlink.room})
        if camlink.sector != "":
            ucam["$set"].update( {"sector": camlink.sector})
        if camlink.link != "":
            ucam["$set"].update({"link": camlink.link})
        return(str(db[f"{client}-cams"].update_one({"id":id},ucam)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
