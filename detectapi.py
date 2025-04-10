from fastapi import FastAPI, HTTPException, File, UploadFile,status
import staindet
from typing import Union
from PIL import Image

app = FastAPI()

@app.get("/detect")
def detectstain(control, current, color = "blue", shape= "auto"):

    #Only for use after module works with pil image inputs.
    # if type(control) == str:
    #     control = staindet._open_image(control)
    # if type(current) == str:
    #     current = staindet._open_image(current)

    staindet.detect(control, current, color, shape)