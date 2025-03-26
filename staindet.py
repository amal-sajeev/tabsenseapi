import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
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

def makeneg(img_array,alpha:float = 0.5):
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

def fuse_image(original, negative, alpha:float = 0.5):
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

def chroma_key(foreground, background, key_color=(0, 0, 0), tolerance=30):
    """
    Perform chroma keying by removing a specific color from the foreground image
    and overlaying it on a background image.
    
    :param foreground: Foreground PIL Image
    :param background: Background PIL Image
    :param key_color: RGB color to be removed (default is black)
    :param tolerance: Color tolerance for chroma keying
    :return: Composited image
    """
    # Increase brightness to 100%
    brightness_enhancer = ImageEnhance.Brightness(foreground)
    foreground = brightness_enhancer.enhance(2.0)  # 2.0 typically brings to full brightness
    
    # Ensure both images are in RGBA mode
    foreground = foreground.convert("RGBA")
    background = background.convert("RGBA")
    
    # Resize background to match foreground if needed
    # Use .copy() to avoid reference issues
    background = background.resize(foreground.size).copy()
    
    # Convert images to numpy arrays for pixel-level manipulation
    fore_array = np.array(foreground)
    
    # Create a mask for the key color
    r, g, b, a = fore_array[:,:,0], fore_array[:,:,1], fore_array[:,:,2], fore_array[:,:,3]
    
    # Calculate the color difference
    color_diff = np.sqrt(
        (r - key_color[0])**2 + 
        (g - key_color[1])**2 + 
        (b - key_color[2])**2
    )
    
    # Create a mask where pixels are within the tolerance
    mask = color_diff <= tolerance
    
    # Make these pixels fully transparent
    fore_array[mask, 3] = 0
    
    # Convert back to PIL Image
    result = Image.fromarray(fore_array)
    
    # Composite the images
    composited = Image.alpha_composite(background, result)
    
    return composited

def detect_color_border(imagepath,color):

    image = cv2.imread(imagepath)
    # Convert to HSV color space for better color detection
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_ranges = {}
    # Define range of green `color in HSV
    color_ranges["lower_green"] = np.array([35, 50, 50])
    color_ranges["upper_green"] = np.array([85, 255, 255])

    # Define range of blue color in HSV
    color_ranges["lower_blue"] = np.array([100, 50, 50])   # Hue: 100-140, Saturation: 50-255, Value: 50-255
    color_ranges["upper_blue"] = np.array([140, 255, 255])

    #Define range of yellow coloor in HSV
    color_ranges["lower_yellow"] = np.array([20, 50, 50])  # Hue: 20-30, Saturation: 50-255, Value: 50-255
    color_ranges["upper_yellow"] = np.array([30, 255, 255])

    # Create a mask for green color
    color_mask = cv2.inRange(hsv, color_ranges[f'lower_{color}'], color_ranges[f'upper_{color}'])

    # Find contours of the green border
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest contour that is likely the border
    border_contour = max(contours, key=cv2.contourArea)

    # Approximate the contour to a polygon
    epsilon = 0.02 * cv2.arcLength(border_contour, True)
    approx = cv2.approxPolyDP(border_contour, epsilon, True)

    return approx

def crop_to_border(image, contour):
    # Get the bounding rectangle of the contour
    x, y, w, h = cv2.boundingRect(contour)

    # Create a mask of the same size as the image
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # Draw the contour on the mask
    cv2.drawContours(mask, [contour], -1, 255, -1)

    # Create a masked image
    masked_image = cv2.bitwise_and(image, image, mask=mask)

    # Crop the image
    cropped = masked_image[y:y+h, x:x+w]

    return cropped

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

imgarr = {"Original":_open_image("imagedata/workstain.jpg")}
imgarr["Negative"]= makeneg(_open_image("imagedata/work.jpg"))
imgarr["Fused"]= fuse_image(imgarr["Original"], imgarr["Negative"], 0.5)
imgarr["FusedEdge"] = imgarr["Fused"].filter(ImageFilter.FIND_EDGES)
image_display(imgarr)