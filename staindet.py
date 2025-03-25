import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def _open_image(image_path:str):
    """Opens an image from disk and converts it into a PIL Image array.

    Args:
        image_path (str): Path to the image
    Returns:
        PIL Image: A float32 Numpy Image array
    """
    img = Image.open(image_path)
    img_array = np.array(img).astype(np.uint8)
    return(img_array)

def makeneg(img_array,alpha : float = 0.5):
    """Takes an image array and converts the array data into its negative. 

    Args:
        img_array (numpy array): Image data array
        alpha (float, optional): Alpha value used to calculate negative. Defaults to 0.5.

    Raises:
        ValueError: _description_
    """
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:  # RGB image
        max_val = 255.0
        negative = max_val - img_array
    elif len(img_array.shape) == 2 or (len(img_array.shape) == 3 and img_array.shape[2] == 1):  # Grayscale
        max_val = 255.0
        negative = max_val - img_array
    else:
        raise ValueError("Unsupported image format")
    negative = np.clip(negative, 0, 255).astype(np.uint8)
    neg_image = Image.fromarray(negative)

    return(neg_image)

def fuse_image(original, negative, alpha):
    """Takes two images, fuses their data, and returns the fused image as a PIL Image.

    Args:
        original (Image): The original image
        negative (Image): The negative image
        alpha (float): The alpha value used to adjust which image the emphasis is placed on.
    """
    ogarray = np.array(original).astype(np.float32)
    negarray = np.array(negative).astype(np.float32)
    fusedarray = alpha * ogarray + (1- alpha) * negarray

    fused = np.clip(fusedarray, 0, 255).astype(np.uint8)
    return(Image.fromarray(fused))

def image_display(arrimg : dict):
    """Given data arrays with the title of the image, create a window displaying the images with their titles in a grid.

    Args:
        arrimg (dict): A dictionary of the data arrays with the image titles as the keys.
    """
    plt.figure(figsize=(15,5))
    columns = len(arrimg.keys())
    pos = 1 
    for key in arrimg.keys():
        plt.subplot(1,columns,pos)
        plt.imshow(arrimg[key])
        plt.title(key)
        plt.axis("off")
        pos += 1
    
    plt.tight_layout()
    plt.show()

imgarr = {"Original":_open_image("wood.jpg")}
imgarr["Negative"]= makeneg(imgarr["Original"])
imgarr["Fused"]= fuse_image(imgarr["Original"], imgarr["Negative"], 0.5)
image_display(imgarr)