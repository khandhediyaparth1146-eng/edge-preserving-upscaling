import numpy as np
from PIL import Image

# Create a 256x256 image
img = np.zeros((256, 256, 3), dtype=np.uint8)

# Background color
img[:, :] = [40, 44, 52]

# Draw a sharp high-contrast white circle
y, x = np.ogrid[:256, :256]
mask = (x - 128)**2 + (y - 128)**2 <= 60**2
img[mask] = [255, 255, 255]

# Draw some sharp diagonal lines
for i in range(256):
    if i % 20 < 5:
        img[i, i] = [255, 0, 0]
        if i < 255: img[i+1, i] = [255, 0, 0]

# Save the image
Image.fromarray(img).save("test_pattern.png")
print("test_pattern.png created")
