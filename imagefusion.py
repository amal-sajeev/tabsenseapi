import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def negativemake(image_path, output_path = None, alpha=0.5):
    """
    Creates a negative of an image and saves it.
    """

    img = Image.open(image_path)

    img_array = np.array(img).astype(np.float32)

    # Create the negative by inverting pixel values
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


    if output_path:
        neg_image.save(output_path)

def fuse_image_with_negative(image_path,neg_path, output_path=None, alpha=0.5):
    """
    Fuses an image with its negative version.

    Parameters:
    image_path (str): Path to the source image
    output_path (str, optional): Path to save the result. If None, won't save.
    alpha (float): Blending factor between original and negative (0.0 to 1.0)

    Returns:
    PIL.Image: The fused image
    """
    # Open the source image
    img = Image.open(image_path)

    #Open the negative Image
    negimg = Image.open(neg_path)

    # Convert to numpy array for easier manipulation
    img_array = np.array(img).astype(np.float32)

    negative = np.array(negimg).astype(np.float32)

    # Blend the original with the negative
    fused = alpha * img_array + (1 - alpha) * negative

    # Convert back to uint8
    fused = np.clip(fused, 0, 255).astype(np.uint8)

    # Create a new image from the array
    fused_img = Image.fromarray(fused)

    # Save if output path is provided
    if output_path:
        fused_img.save(output_path)

    return fused_img

def display_images(original_path, stain_path, neg_path, alpha=0.5):
    """
    Displays the original image, its negative, and the fused result.
    First row: original, stained, negative, stained+negative fusion
    Second row: original, negative, original+negative fusion
    """
    # Open original image
    original = Image.open(original_path)
    # Open stain image
    stained = Image.open(stain_path)
    # Open negative image
    negative = Image.open(neg_path)

    # Create fused images
    stained_neg_fused = fuse_image_with_negative(stain_path, neg_path, alpha=alpha)
    orig_neg_fused = fuse_image_with_negative(original_path, neg_path, alpha=alpha)

    # Display all images
    plt.figure(figsize=(15, 10))

    # First row
    plt.subplot(2, 4, 1)
    plt.imshow(original)
    plt.title("Original")
    plt.axis('off')

    plt.subplot(2, 4, 2)
    plt.imshow(stained)
    plt.title("Stained")
    plt.axis('off')

    plt.subplot(2, 4, 3)
    plt.imshow(negative)
    plt.title("Negative")
    plt.axis('off')

    plt.subplot(2, 4, 4)
    plt.imshow(stained_neg_fused)
    plt.title(f"Stained+Negative (α={alpha})")
    plt.axis('off')

    # Second row
    plt.subplot(2, 4, 5)
    plt.imshow(original)
    plt.title("Original")
    plt.axis('off')

    plt.subplot(2, 4, 6)
    plt.imshow(negative)
    plt.title("Negative")
    plt.axis('off')

    plt.subplot(2, 4, 7)
    plt.imshow(orig_neg_fused)
    plt.title(f"Original+Negative (α={alpha})")
    plt.axis('off')

    plt.tight_layout()
    plt.show()

# Wood Example

# image_path = "wood.jpg"
# neg_path = "woodneg.jpg"
# stain_path = "woodstain.jpg"
#
# neg_image = negativemake(image_path, "woodneg.jpg")
#
# # Create and save the fused image
# # fused_img = fuse_image_with_negative(image_path, neg_path, "fused_result.jpg")
#
# # Display comparison of original, negative and fused
# display_images(image_path, stain_path, neg_path, alpha=0.5)

#Marble Example

# image_path = "marble.jpg"
# neg_path = "marbleneg.jpg"
# stain_path = "marblestain.jpg"
#
# neg_image = negativemake(image_path, "marbleneg.jpg")

#Dark Table Example

image_path = "darktable.jpg"
neg_path = "darktableneg.jpg"
stain_path = "darktablestain.jpg"

neg_image = negativemake(image_path, neg_path)

# Create and save the fused image
# fused_img = fuse_image_with_negative(image_path, neg_path, "fused_result.jpg")

# Display comparison of original, negative and fused
display_images(image_path, stain_path, neg_path, alpha=0.5)
