"""
Quick coordinate finder.
Opens the screenshot and shows x,y position + RGB under the cursor.

Usage:
    pip install matplotlib  # run this first if not installed
    python find_coords.py path/to/screenshot.png
"""

import sys
import cv2
import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Install matplotlib first: pip install matplotlib")
    sys.exit(1)


def onclick(event):
    x, y = int(event.xdata), int(event.ydata)
    img = event.canvas.figure._img_data
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
        b, g, r = img[y, x]
        h, w = img.shape[:2]
        print(
            f"Position: ({x:4d}, {y:4d})  "
            f"Ratio: ({x/w:.3f}, {y/h:.3f})  "
            f"RGB: ({r:3d}, {g:3d}, {b:3d})"
        )


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\HP\Downloads\1000417657.png"
    img = cv2.imread(path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig, ax = plt.subplots(figsize=(10, 20))
    ax.imshow(img_rgb)
    fig._img_data = img
    fig.canvas.mpl_connect("button_press_event", onclick)
    print("Click anywhere on the image to see coordinates.")
    print(f"Image size: {img.shape[1]}x{img.shape[0]}")
    print("Press Ctrl+C in terminal or close window to exit.")
    plt.tight_layout()
    plt.show()
