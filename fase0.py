import cv2
import numpy as np
from skimage import color
import matplotlib.pyplot as plt

# --- 1. Open the video and grab one frame per second ---
video = cv2.VideoCapture("test-trailer.mp4")
fps = video.get(cv2.CAP_PROP_FPS)   # how many frames per second the video has
print(f"The video runs at {fps:.1f} frames per second")

frames = []
count = 0
while True:
    ok, frame = video.read()
    if not ok:
        break                        # video finished
    if count % int(fps) == 0:        # keep one frame every second
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame_rgb)
    count += 1
video.release()
print(f"Extracted {len(frames)} frames, one per second")

# --- 2. For each frame, compute brightness and colour temperature ---
brightness = []
temperature = []
mean_colours = []
for f in frames:
    lab = color.rgb2lab(f / 255.0)   # convert to LAB colour space
    L = lab[:, :, 0].mean()          # lightness: how bright the frame is
    a = lab[:, :, 1].mean()          # green-red axis
    b = lab[:, :, 2].mean()          # blue-yellow axis
    brightness.append(L)
    temperature.append(b)            # positive b = warm, negative = cool
    mean_colours.append(f.reshape(-1, 3).mean(axis=0) / 255.0)

# --- 3. Draw the curves and the barcode ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8))

ax1.plot(brightness, color="black")
ax1.set_title("Brightness over time (higher = lighter)")
ax1.set_xlabel("seconds")

ax2.plot(temperature, color="orangered")
ax2.set_title("Colour temperature over time (higher = warmer)")
ax2.set_xlabel("seconds")

# the barcode: one coloured stripe per second
barcode = np.array(mean_colours).reshape(1, len(mean_colours), 3)
ax3.imshow(barcode, aspect="auto")
ax3.set_title("Movie barcode")
ax3.set_yticks([])

plt.tight_layout()
plt.savefig("fase0-result.png", dpi=100)
plt.show()
print("Done! Check the file fase0-result.png")