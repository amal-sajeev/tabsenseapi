from fastapi import FastAPI, HTTPException, File, UploadFile,status
import staindet
from typing import Union
from PIL import Image

app = FastAPI()

@app.get("/detect")
def detectstain(control, current, crop:bool=True, color = "blue", shape= "auto", format:str="png"):

    #Only for use after module works with pil image inputs.
    # if type(control) == str:
    #     control = staindet._open_image(control)
    # if type(current) == str:
    #     current = staindet._open_image(current)

    try:
        return(staindet.detect(
            control = f"imagedata/{control}.{format}",
            current = f"imagedata/{current}.{format}",
            crop = crop,
            color = color,
            shape = shape)
            )
    except Exception as e:
        return(e)
