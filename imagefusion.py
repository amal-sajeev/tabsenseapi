import cv2
import numpy as np

def detect_and_crop_color_border(image, color='blue'):
    """
    Detect and crop colored border with improved robustness.
    
    Args:
        image (numpy.ndarray): Input image
        color (str): Color of the border to detect
    
    Returns:
        numpy.ndarray: Cropped image
    """
    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
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
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    
    # Fill the convex hull on the mask
    cv2.fillPoly(mask, [hull], 255)
    
    # Bitwise AND to keep only the area inside the border
    result = cv2.bitwise_and(image, image, mask=mask)
    
    return result

def process_image(input_path, output_path, color='blue'):
    """
    Process an image by detecting and cropping to a colored border.
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save processed image
        color (str, optional): Border color to detect. Defaults to 'blue'.
    """
    try:
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Could not read image from {input_path}")
        
        # Crop to colored border
        cropped_image = detect_and_crop_color_border(image, color)
        
        # Save the cropped image
        cv2.imwrite(output_path, cropped_image)
        print(f"Image cropped successfully and saved to {output_path}")
    
    except Exception as e:
        print(f"Error processing image: {e}")

# Example usage
if __name__ == "__main__":
    process_image('bluemult.png', 'cropped_blueblock.png', color='blue')