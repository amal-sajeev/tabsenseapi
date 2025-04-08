import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
import matplotlib.pyplot as plt
from scipy import ndimage

def detect_and_crop_color_border(image, color='blue'):
    """
    Detect and crop colored border with improved robustness.
    
    Args:
        image (PIL.Image): Input image
        color (str): Color of the border to detect
    
    Returns:
        PIL.Image: Cropped image
    """
    # Convert PIL Image to numpy array
    np_image = np.array(image)
    
    # Convert to BGR for OpenCV (PIL uses RGB)
    cv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    
    # Color ranges in HSV
    color_ranges = {
        "green": ([35, 50, 50], [85, 255, 255]),
        "blue": ([100, 50, 50], [140, 255, 255]),
        "yellow": ([20, 50, 50], [30, 255, 255])
    }
    
    # Get color range
    lower, upper = color_ranges.get(color, color_ranges['blue'])
    
    # Create mask for specified color
    color_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    
    # Find contours of colored border
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image  # Return original image if no border found
    
    # Find the largest contour (presumably the border)
    border_contour = max(contours, key=cv2.contourArea)
    
    # Get convex hull to smooth out irregularities
    hull = cv2.convexHull(border_contour)
    
    # Create a mask for the entire image
    mask = np.zeros(cv_image.shape[:2], dtype=np.uint8)
    
    # Fill the convex hull on the mask
    cv2.fillPoly(mask, [hull], 255)
    
    # Bitwise AND to keep only the area inside the border
    result = cv2.bitwise_and(cv_image, cv_image, mask=mask)
    
    # Convert back to RGB for PIL
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    
    # Convert back to PIL Image
    return Image.fromarray(result_rgb)

def process_image(image, color='blue'):
    """
    Process an image by detecting and cropping to a colored border.
    
    Args:
        image (PIL.Image): Input image
        color (str, optional): Border color to detect. Defaults to 'blue'.
    
    Returns:
        PIL.Image: Cropped image
    """
    try:
        # Crop to colored border
        cropped_image = detect_and_crop_color_border(image, color)
        
        return cropped_image
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return image

def _open_image(image_path:str, use_border : bool = False, color : str = "blue"):
    """Opens an image from disk and converts it into a PIL Image array.

    Args:
        image_path (str): Path to the image
    Returns:
        PIL Image: A float32 Numpy Image array
    """
    img = Image.open(image_path)
    if use_border:
        img = process_image(img)
    return(img)

def makeneg(img_array,alpha:float = 0.5):
    """Takes an image array and converts the array data into its negative. 

    Args:
        img_array (numpy array): Image data array
        alpha (float, optional): Alpha value used to calculate negative. Defaults to 0.5.

    Raises:
        ValueError: _description_
    """
    img_array = np.array(img_array).astype(np.uint8)
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
    fuseimage = Image.fromarray(fused).filter(ImageFilter.FIND_EDGES)
    border = (25,25,25,25)
    return(ImageOps.crop(fuseimage,border))

def detect_stain(image, threshold=1):
    """
    Detect if an image contains any non-black pixels.
    
    Parameters:
    - image: PIL Image object
    - threshold: Maximum pixel value to still be considered "black" 
                 (allows for slight variations due to compression)
    
    Returns:
    - Boolean: True if image contains non-black pixels, False otherwise
    """
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Handle both color and grayscale images
    if len(img_array.shape) == 3:
        # For color images, check if any pixel in any channel exceeds threshold
        return np.any(img_array > threshold)
    elif len(img_array.shape) == 2:
        # For grayscale images, check if any pixel exceeds threshold
        return np.any(img_array > threshold)
    else:
        # Unexpected image format
        raise ValueError("Unsupported image format")

def highlight_stain(fused_image, draw_image, num_sectors=5, border_color=(255, 0, 0), border_width=3):
    """
    Divides the image into square sectors and finds the one with the highest concentration of non-black pixels.
    
    Args:
        fused_image: PIL Image - The input image to analyze,
        draw_image: PIL Image - The input image to highlight the stain on
        num_sectors: int - Number of sectors to divide the image into (both horizontally and vertically)
        border_color: tuple - RGB color for the border (default: blue)
        border_width: int - Width of the border in pixels
        
    Returns:
        PIL Image with a border drawn around the sector with highest non-black pixel concentration
    """
    import numpy as np
    from PIL import Image, ImageDraw
    
    # Convert the image to numpy array for easier processing
    img_array = np.array(fused_image)
    
    # Get image dimensions
    height, width = img_array.shape[:2]
    
    # Calculate sector dimensions
    sector_height = height // num_sectors
    sector_width = width // num_sectors
    
    # Track the highest density sector
    max_density = 0
    max_sector = (0, 0)  # (row, col)
    
    # Define threshold for non-black pixels (adjust as needed)
    # For grayscale images
    if len(img_array.shape) == 2:
        threshold = 10  # Any pixel value above this is considered non-black
        
        # Analyze each sector
        for row in range(num_sectors):
            for col in range(num_sectors):
                # Define sector boundaries
                start_y = row * sector_height
                end_y = start_y + sector_height
                start_x = col * sector_width
                end_x = start_x + sector_width
                
                # Extract sector
                sector = img_array[start_y:end_y, start_x:end_x]
                
                # Count non-black pixels
                non_black_count = np.sum(sector > threshold)
                
                # Calculate density (percentage of non-black pixels)
                density = non_black_count / (sector_height * sector_width)
                
                # Update if this sector has higher density
                if density > max_density:
                    max_density = density
                    max_sector = (row, col)
    
    # For RGB images
    else:
        threshold = 10  # Any pixel where sum of RGB values is above this is considered non-black
        
        # Analyze each sector
        for row in range(num_sectors):
            for col in range(num_sectors):
                # Define sector boundaries
                start_y = row * sector_height
                end_y = start_y + sector_height
                start_x = col * sector_width
                end_x = start_x + sector_width
                
                # Extract sector
                sector = img_array[start_y:end_y, start_x:end_x]
                
                # Count non-black pixels (sum of RGB channels > threshold)
                if len(img_array.shape) == 3:
                    non_black_count = np.sum(np.sum(sector, axis=2) > threshold)
                else:
                    non_black_count = np.sum(sector > threshold)
                
                # Calculate density
                density = non_black_count / (sector_height * sector_width)
                
                # Update if this sector has higher density
                if density > max_density:
                    max_density = density
                    max_sector = (row, col)
    
    # Create a copy of the original image to draw on
    result_image = draw_image
    draw = ImageDraw.Draw(draw_image)
    
    # Get coordinates of the highest density sector
    row, col = max_sector
    start_y = row * sector_height
    end_y = start_y + sector_height - 1
    start_x = col * sector_width
    end_x = start_x + sector_width - 1
    
    # Draw border around the sector
    for i in range(border_width):
        draw.rectangle(
            [(start_x-i, start_y-i), (end_x+i, end_y+i)],
            outline=border_color
        )
    
    return result_image

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

def detect(control:str, current:str):
    #Import original image
    imgarr = {"Original":_open_image(control,True,"blue")}
    imgarr["Negative"]= makeneg(imgarr["Original"])
    imgarr["Current"] = _open_image(current,True,"blue")
    imgarr["Fused"]= fuse_image(imgarr["Current"], imgarr["Negative"], 0.5)
    # imgarr["FusedEdge"] = imgarr["Fused"].filter(ImageFilter.FIND_EDGES)
    imgarr["Fused"].save("edgetest", "png")
    print(np.array(imgarr["Fused"]).astype(int))
    imgarr["Highlighted"] = highlight_stain(imgarr["Fused"], imgarr["Current"], 5)
    image_display(imgarr)

detect("imagedata/blue.jpg","imagedata/bluestain.jpg")