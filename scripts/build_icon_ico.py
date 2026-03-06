# Convert assets/icon.png to assets/icon.ico for Windows exe icon.
# Run from project root. Requires Pillow: pip install Pillow

import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
png_path = os.path.join(root, "assets", "icon.png")
ico_path = os.path.join(root, "assets", "icon.ico")

if not os.path.isfile(png_path):
    print("assets/icon.png not found, skipping ico generation.")
    sys.exit(0)

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

img = Image.open(png_path).convert("RGBA")
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(ico_path, format="ICO", sizes=sizes)
print("Generated assets/icon.ico")
