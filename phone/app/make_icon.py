# Draws the app icon (a green board with the 7 gold TOH contacts) at the Sailfish launcher sizes.
# Usage: python3 make_icon.py <out_dir>   -> <out_dir>/<size>x<size>/toh-devkit.png
import os, sys
from PIL import Image, ImageDraw
out = sys.argv[1]
PINS = [(0, 0), (1, 0), (2, 0), (3, 0), (0.5, 1), (1.5, 1), (2.5, 1)]   # 4 + 3, 2.90 mm pitch, as seen from behind
for size in (86, 108, 128, 172):
    S = size * 4                                                         # draw large, scale down for smooth edges
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([S * .04, S * .04, S * .96, S * .96], radius=S * .22, fill=(40, 110, 70, 255))
    p, r = S * .2, S * .075
    x0, y0 = S / 2 - 1.5 * p, S / 2 - 0.5 * p
    for i, (cx, cy) in enumerate(PINS):
        x, y = x0 + cx * p, y0 + cy * p
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 190, 70, 255))
    os.makedirs(f"{out}/{size}x{size}", exist_ok=True)
    im.resize((size, size), Image.LANCZOS).save(f"{out}/{size}x{size}/toh-devkit.png")
print("icons in", out)
