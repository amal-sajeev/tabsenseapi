import cv2
import numpy as np
from PIL import Image

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

# Example usage
if __name__ == "__main__":
    # Load image using PIL
    input_image = Image.open('blueblock.png')
    
    # Process the image
    processed_image = process_image(input_image, color='blue')
    
    # Save the processed image
    processed_image.save('cropped_blueblock.png')
    print("Image processed successfully!")