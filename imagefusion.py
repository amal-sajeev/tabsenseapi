import cv2
import numpy as np

def detect_color_border(image,color):
    # Convert to HSV color space for better color detection
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_ranges = {}
    # Define range of green `color in HSV
    color_ranges["lower_green"] = np.array([35, 50, 50])
    color_ranges["upper_green"] = np.array([85, 255, 255])

    # Define range of blue color in HSV
    color_ranges["lower_blue"] = np.array([100, 50, 50])   # Hue: 100-140, Saturation: 50-255, Value: 50-255
    color_ranges["upper_blue"] = np.array([140, 255, 255])

    #Define range of yellow color in HSV
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

# Read the image
image = cv2.imread('blueblock.png')

# Detect green border
green_border_contour = detect_color_border(image, "blue")

# Crop the image
cropped_image = crop_to_border(image, green_border_contour)

# Save the cropped image
cv2.imwrite('cropped_blackbord.png', cropped_image)
print("Image cropped successfully!")
