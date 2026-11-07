# Clip positions: Jolla's cover (toh-3d-model) vs the cTOH-M frame, both seen from inside (side wall at the
# phone's right edge = left in the picture). Clip boxes found by slicing above the plate (u, v phone coords).
# Usage: python3 clips_compare.py <jolla-inside.png (12 px/mm, 84x166 view)> <ctohm-inside.png (8 px/mm)> <out.png>
import sys
from PIL import Image, ImageDraw, ImageFont
fj, fc, out = sys.argv[1:4]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f22 = ImageFont.truetype(F, 22); b26, b34 = ImageFont.truetype(FB, 26), ImageFont.truetype(FB, 34)
RED, BLUE, INK, GREEN = (210, 30, 80), (30, 90, 200), (25, 25, 30), (20, 140, 60)
j = Image.open(fj).convert("RGB"); j = j.resize((j.width * 2 // 3, j.height * 2 // 3), Image.LANCZOS)   # -> 8 px/mm
c = Image.open(fc).convert("RGB")
PPM, gap, top = 8, 80, 110
W = j.width + c.width + gap + 200; H = top + j.height + 230
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
offs = {"j": (40, top), "c": (40 + j.width + gap, top)}
cv.paste(j, offs["j"]); cv.paste(c, offs["c"])
def P(k, u, v):   # inside view: x grows with u (u=37 at the centre), y: v=78.5 at the centre
    ox, oy = offs[k]; return ox + j.width / 2 + (u - 37) * PPM, oy + j.height / 2 - (v - 78.5) * PPM
def box(k, u0, u1, v0, v1, col, lab=None):
    x0, y1 = P(k, u0 - 1.2, v0 - 1.2); x1, y0 = P(k, u1 + 1.2, v1 + 1.2)
    d.rectangle([x0, y0, x1, y1], outline=col, width=5)
    if lab: d.text((x1 + 6, (y0 + y1) / 2), lab, fill=col, font=b26, anchor="lm")
JOLLA = [((11.3, 15.1, 1.6, 2.6), "bottom"), ((48.8, 50.9, 1.5, 2.4), "bottom"), ((15.8, 18.4, 154.7, 155.7), "top"),
         ((56.3, 58.9, 154.7, 155.7), "top"), ((16.5, 20.3, 113.5, 114.9), "middle"), ((38.3, 39.4, 9.5, 12.4), "middle (you measured)")]
for (u0, u1, v0, v1), lab in JOLLA: box("j", u0, u1, v0, v1, RED, lab)
CT = [(0.9, 1.5, v0, v1) for v0, v1 in ((1.3, 4.0), (27.5, 30.1), (53.8, 56.4), (76.5, 78.8), (113.7, 116.3), (134.7, 136.8), (152.9, 155.5))] + \
     [(72.5, 73.1, v0, v1) for v0, v1 in ((1.5, 3.5), (22.0, 24.7), (53.5, 56.1), (136.8, 138.8), (152.9, 155.6))]
for u0, u1, v0, v1 in CT: box("c", u0, u1, v0, v1, BLUE)
for (u0, u1, v0, v1), lab in JOLLA[:2] + JOLLA[4:]: box("c", u0, u1, v0, v1, (170, 170, 175))
d.text((offs["j"][0], 20), "Jolla cover (your Inari Blue), inside", fill=RED, font=b34)
d.text((offs["c"][0], 20), "cTOH-M (our dev cover), inside", fill=BLUE, font=b34)
d.text((offs["j"][0], 62), "red = clips standing up from the plate (plus hooks along the rims)", fill=INK, font=f22)
d.text((offs["c"][0], 62), "blue = the 12 hooks on the long sides; grey = where Jolla has clips", fill=INK, font=f22)
y = top + j.height + 20
for t in ["cTOH-M holds the cover only with 12 hooks along the two long sides (7 + 5), the outer ones near the corners.",
          "Jolla's cover also has 2 bottom, 2 top and 2 middle clips; two of them sit right next to the contact pads.",
          "cTOH-M has no clips there (at the bottom one and the one you measured it has 1 mm deep recesses instead).",
          "Risk for the dev cover: nothing presses the plate down right at the pads, so the 7 springs may bow it away.",
          "Test print first; if contacts are flaky, add those two clips (or a stiffening rib) near the indent."]:
    d.text((40, y), t, fill=INK, font=f22); y += 34
cv.crop((0, 0, W, y + 20)).save(out); print(out)
