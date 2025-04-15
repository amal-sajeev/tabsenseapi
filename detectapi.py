from fastapi import FastAPI, HTTPException, File, UploadFile,status
import staindet
from typing import Union
from PIL import Image

app = FastAPI()

@app.get("/detect")
def detectstain(control, current, crop:bool=True, crop_color = "blue", crop_shape= "auto", format:str="png"):
    """Endpoint that reads a control image, the current image, and by comparing the two detects whether there's a stain on the current surface. If the tables aren't captured properly, as long as there's a coloured border on the surfaces, the crop parameter can be used to isolate the surface.

    Args:
        control (string): Filename of control image, which is the clean surface under the current conditions.
        current (string): Filename of current image, the most recent image of the surface.
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
        return(staindet.detect(
            control = f"imagedata/{control}.{format}",
            current = f"imagedata/{current}.{format}",
            crop = crop,
            color = crop_color,
            shape = crop_shape)
            )
    except Exception as e:
        return(e)

