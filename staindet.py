import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
import matplotlib.pyplot as plt
from scipy import ndimage
from typing import Union

def detect_and_crop_color_border(image, color='blue', shape='auto'):
    """
    Detect and crop colored border with improved robustness for various shapes.
    
    Args:
        image (PIL.Image): Input image
        color (str): Color of the border to detect
        shape (str): Shape of the border ('auto', 'rectangle', 'circle', 'oval')
    
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
        "yellow": ([20, 50, 50], [30, 255, 255]),
        "red1": ([0, 50, 50], [10, 255, 255]),  # Red spans across 0 degrees in HSV
        "red2": ([170, 50, 50], [180, 255, 255])  # Need to check both ranges
    }
    
    # Get color range
    if color == "red":
        # For red, we need to combine two masks
        lower1, upper1 = color_ranges["red1"]
        lower2, upper2 = color_ranges["red2"]
        
        # Create masks for both red ranges
        color_mask1 = cv2.inRange(hsv, np.array(lower1), np.array(upper1))
        color_mask2 = cv2.inRange(hsv, np.array(lower2), np.array(upper2))
        
        # Combine the masks
        color_mask = cv2.bitwise_or(color_mask1, color_mask2)
    else:
        # For other colors
        lower, upper = color_ranges.get(color, color_ranges['blue'])
        color_mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    
    # Apply morphological operations to clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours of colored border
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image  # Return original image if no border found
    
    # Find the largest contour (presumably the border)
    border_contour = max(contours, key=cv2.contourArea)
    
    # Create a mask for the entire image
    mask = np.zeros(cv_image.shape[:2], dtype=np.uint8)
    
    # Handle different shapes
    if shape == 'auto':
        # Improved shape detection
        
        # Calculate shape metrics
        area = cv2.contourArea(border_contour)
        perimeter = cv2.arcLength(border_contour, True)
        
        # Fit an enclosing circle
        (center_x, center_y), radius = cv2.minEnclosingCircle(border_contour)
        circle_area = np.pi * radius * radius
        
        # Fit an ellipse (if possible)
        if len(border_contour) >= 5:
            ellipse = cv2.fitEllipse(border_contour)
            ellipse_axes = ellipse[1]  # Major and minor axes
            ellipse_area = np.pi * ellipse_axes[0]/2 * ellipse_axes[1]/2
            
            # Calculate aspect ratio of the ellipse
            aspect_ratio = max(ellipse_axes) / min(ellipse_axes)
        else:
            ellipse = None
            ellipse_area = float('inf')
            aspect_ratio = float('inf')
        
        # Calculate circularity: 4*pi*area/perimeter^2
        # Perfect circle has circularity of 1
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Calculate how well the contour fits a circle
        circle_similarity = area / circle_area if circle_area > 0 else 0
        
        # Determine shape based on metrics
        if circularity > 0.85 and circle_similarity > 0.9:
            # It's likely a circle
            center = (int(center_x), int(center_y))
            radius = int(radius)
            cv2.circle(mask, center, radius, 255, -1)
            print("Detected shape: Circle")
            
        elif ellipse is not None and aspect_ratio < 1.5 and area / ellipse_area > 0.9:
            # It's likely an oval/ellipse that's not too elongated
            cv2.ellipse(mask, ellipse, 255, -1)
            print("Detected shape: Oval/Ellipse")
            
        else:
            # It's likely a polygon or irregular shape
            # Try to approximate the polygon
            epsilon = 0.02 * perimeter
            approx = cv2.approxPolyDP(border_contour, epsilon, True)
            
            if len(approx) == 4:
                # It might be a rectangle
                cv2.fillPoly(mask, [approx], 255)
                print("Detected shape: Rectangle/Square")
            else:
                # Use convex hull for irregular shapes
                hull = cv2.convexHull(border_contour)
                cv2.fillPoly(mask, [hull], 255)
                print(f"Detected shape: Irregular polygon with {len(approx)} points")
    
    elif shape == 'circle':
        # Fit a circle to the contour
        (x, y), radius = cv2.minEnclosingCircle(border_contour)
        center = (int(x), int(y))
        radius = int(radius)
        cv2.circle(mask, center, radius, 255, -1)
    
    elif shape == 'oval' or shape == 'ellipse':
        # Fit an ellipse to the contour
        if len(border_contour) >= 5:  # Need at least 5 points to fit ellipse
            ellipse = cv2.fitEllipse(border_contour)
            cv2.ellipse(mask, ellipse, 255, -1)
        else:
            # Fallback to convex hull if not enough points
            hull = cv2.convexHull(border_contour)
            cv2.fillPoly(mask, [hull], 255)
    
    elif shape == 'rectangle':
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(border_contour)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    
    else:  # Default: use contour as is
        # Use convex hull for smoother result
        hull = cv2.convexHull(border_contour)
        cv2.fillPoly(mask, [hull], 255)
    
    # Bitwise AND to keep only the area inside the border
    result = cv2.bitwise_and(cv_image, cv_image, mask=mask)
    
    # Convert back to RGB for PIL
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    
    # Convert back to PIL Image
    return Image.fromarray(result_rgb)

def process_image(image, color='blue', shape='auto'):
    """
    Process an image by detecting and cropping to a colored border.
    
    Args:
        image (PIL.Image): Input image
        color (str, optional): Border color to detect. Defaults to 'blue'.
        shape (str, optional): Shape of the border to detect. Defaults to 'auto'.
    
    Returns:
        PIL.Image: Cropped image
    """
    try:
        # Crop to colored border
        cropped_image = detect_and_crop_color_border(image, color, shape)
        
        return cropped_image
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return image

def _open_image(image_path:str, use_border : bool = False, color : str = "blue", shape : str = "auto"):
    """Opens an image from disk and converts it into a PIL Image array.

    Args:
        image_path (str): Path to the image
        use_border (bool, optional): Whether to detect and crop to border. Defaults to False.
        color (str, optional): Color of the border to detect. Defaults to "blue".
        shape (str, optional): Shape of the border ('auto', 'rectangle', 'circle', 'oval'). Defaults to "auto".
    Returns:
        PIL Image: A float32 Numpy Image array
    """
    img = Image.open(image_path)
    if use_border:
        img = process_image(img, color, shape)
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
    result_image = draw_image.copy()
    draw = ImageDraw.Draw(result_image)
    
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

def image_display(arrimg: dict, colno: int, figsize: tuple = (15, 5), detected: bool = False):
    """Given data arrays with the title of the image, create a window displaying the images with their titles in a grid.
    Displays an optional text at the bottom middle of the figure.

    Args:
        arrimg (dict): A dictionary of the data arrays with the image titles as the keys.
        colno (int): Number of columns.
        figsize (tuple): Size of the display window, as (width, height).
        display_text (str): Text to display at the bottom middle of the layout.
    """
    import math
    import matplotlib.pyplot as plt
    
    if detected:
        display_text = "STAIN DETECTED"
    else:
        display_text = "CLEAN"

    fig = plt.figure(figsize=figsize)
    columns = colno
    rows = math.ceil(len(arrimg.keys()) / colno)
    pos = 1
    
    for key in arrimg.keys():
        plt.subplot(rows, columns, pos)
        plt.imshow(arrimg[key])
        plt.title(key)
        plt.axis("off")
        pos += 1
    
    # Add the text at the bottom middle of the figure
    if display_text:
        fig.text(0.5, 0.01, display_text, ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # Adjust layout to make room for the text
    plt.show()
 
def detect(control:str, current:str, crop:bool=True, color:str="blue", shape:str="auto", displayresults:bool=True):
    #Import original image
    imgarr = {"Control":_open_image(control, False)}
    imgarr["Current"] = _open_image(current, False)
    if crop:
        imgarr["Cropped Control"] = process_image(imgarr["Control"], color, shape)
        imgarr["Cropped Current"] = process_image(imgarr["Current"], color, shape)
        imgarr["Fused"] = fuse_image(
            original= imgarr["Cropped Current"],
            negative= makeneg(imgarr["Cropped Control"]),
            alpha=0.5
        )
    else:
        imgarr["Control"] = process_image(imgarr["Control"], color, shape)
        imgarr["Current"] = process_image(imgarr["Current"], color, shape)
        imgarr["Fused"] = fuse_image(
            original= imgarr["Current"],
            negative= makeneg(imgarr["Control"]),
            alpha=0.5
        )
    detected = detect_stain(imgarr["Fused"],1)
    if detected:
        imgarr["Highlighted Result"] = highlight_stain(
            fused_image=imgarr["Fused"],
            draw_image=imgarr["Current"],
            num_sectors=5,
            border_color=(255,0,0),
            border_width=4
        )
    if displayresults:
        image_display(imgarr,2,(5,7), detected= detect_stain(imgarr["Fused"],1))
    return(str(detected))

if __name__ == "__main__":
    # Example usage:
    # detect("imagedata/bluesplit.png", "imagedata/bluesplitstain.png", "bluesplit", "circle")
    # detect("imagedata/bluesplit.png", "imagedata/bluesplitstain.png", "bluesplit", "oval")
    # Or use auto detection:
    detect("imagedata/bluesplit.png", "imagedata/bluesplitstain.png", "bluesplit", "auto")