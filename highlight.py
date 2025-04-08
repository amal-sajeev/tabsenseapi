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

def find_highest_density_sector(fused_image, num_sectors=5, border_color=(0, 0, 255), border_width=3):
    """
    Divides the image into square sectors and finds the one with the highest concentration of non-black pixels.
    
    Args:
        fused_image: PIL Image - The input image to analyze
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
    result_image = fused_image.copy()
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