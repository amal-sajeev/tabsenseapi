import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

def highlight_non_black_concentrated_region(test_image, target_image, border_width=2, border_color=(255, 0, 0)):
    """
    Detects the most concentrated region of non-black pixels and draws a border 
    around this region on the target image.
    
    Args:
        test_image (PIL.Image): Image to check for non-black pixels
        target_image (PIL.Image): Image to draw borders on
        border_width (int): Width of the border in pixels
        border_color (tuple): RGB color of the border
    
    Returns:
        PIL.Image: Target image with red border around the most concentrated non-black region
    """
    # Ensure images are the same size
    if test_image.size != target_image.size:
        raise ValueError("Test and target images must be the same dimensions")
    
    # Convert test image to numpy array
    test_array = np.array(test_image)
    
    # Create a copy of the target image to draw on
    highlighted_image = target_image.copy()
    draw = ImageDraw.Draw(highlighted_image)
    
    # Handle different image modes
    if len(test_array.shape) == 2:  # Grayscale image
        non_black_mask = test_array > 0
    elif len(test_array.shape) == 3:  # RGB or RGBA image
        non_black_mask = np.any(test_array > 0, axis=2)
    else:
        raise ValueError("Unsupported image mode")
    
    # If no non-black pixels found, return the original image
    if not np.any(non_black_mask):
        return highlighted_image
    
    # Label connected regions
    labeled_array, num_features = ndimage.label(non_black_mask)
    
    # If no features found, return the original image
    if num_features == 0:
        return highlighted_image
    
    # Find the size of each region
    region_sizes = np.bincount(labeled_array.ravel())[1:]
    
    # Find the label of the largest region
    largest_region_label = np.argmax(region_sizes) + 1
    
    # Create a mask for the largest region
    largest_region_mask = labeled_array == largest_region_label
    
    # Find the bounding box of the largest region
    region_coords = np.column_stack(np.where(largest_region_mask))
    min_y, min_x = region_coords.min(axis=0)
    max_y, max_x = region_coords.max(axis=0)
    
    # Add a small padding
    padding = 3
    min_y = max(0, min_y - padding)
    min_x = max(0, min_x - padding)
    max_y = min(target_image.height - 1, max_y + padding)
    max_x = min(target_image.width - 1, max_x + padding)
    
    # Draw a red rectangle border
    draw.rectangle(
        [(min_x, min_y), (max_x, max_y)], 
        outline=border_color, 
        width=border_width
    )
    
    return highlighted_image

# Example usage
def test_concentrated_border_detection():
    # Create a black test image with multiple white regions
    test_image = Image.new('RGB', (200, 200), color=(0, 0, 0))
    draw = ImageDraw.Draw(test_image)
    
    # Draw some white regions of different sizes
    draw.rectangle([(20, 20), (40, 40)], fill=(255, 255, 255))  # Small region
    draw.rectangle([(50, 50), (120, 120)], fill=(255, 255, 255))  # Larger region
    draw.rectangle([(150, 150), (180, 180)], fill=(255, 255, 255))  # Another small region
    
    # Create a target image (could be any image you want to mark)
    target_image = Image.new('RGB', (200, 200), color=(200, 200, 200))
    
    # Apply the highlighting function
    result_image = highlight_non_black_concentrated_region(test_image, target_image)
    
    # Optionally save or display the result
    test_image.save("test_image.png")
    result_image.save('concentrated_highlighted_image.png')
    print("Image saved with red border around the most concentrated non-black region")
    
    return result_image

test_concentrated_border_detection()