# Wiring diagram: contact board wire pads (seen from outside, through the cover's slot) -> breakout board wire holes.
# Colour-coded: each slot pad has the colour of the breakout hole its wire goes to.
# Pad positions from pcb/contact/make_board.py (WIRE); hole/header pixel positions measured on renders/breakout.png.
# Usage (repo root): python3 scripts/wiring_sheet.py renders/wiring.png
import sys
from PIL import Image, ImageDraw, ImageFont
res = sys.argv[1]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f24, b26, b30, b34, b44 = ImageFont.truetype(F, 24), ImageFont.truetype(FB, 26), ImageFont.truetype(FB, 30), ImageFont.truetype(FB, 34), ImageFont.truetype(FB, 44)
INK, GREY, RED, BLUE, PLASTIC, MASK = (25, 25, 30), (110, 110, 120), (210, 30, 80), (30, 90, 200), (150, 152, 158), (40, 95, 60)
WIRE = {7: (32.9, 11.75), 5: (30.6, 11.75), 3: (28.3, 11.75), 1: (26.0, 11.75),
        6: (27.15, 10.25), 4: (29.45, 10.25), 2: (31.75, 10.25)}
NAME = {1: "VIN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V"}
COL = {"5V": (220, 40, 40), "GND": (30, 30, 30), "SDA": (40, 110, 230), "SCL": (240, 190, 20), "INT": (40, 170, 70), "ID": (250, 250, 250)}
TXT = {"5V": "white", "GND": "white", "SDA": "white", "SCL": INK, "INT": "white", "ID": INK}
HOLE_X = dict(zip(["5V", "GND", "SDA", "SCL", "INT", "ID"], [437, 521, 606, 691, 776, 861]))
HOLE_Y, HDR_Y = 220, 622

bo = Image.open("renders/breakout.png").convert("RGBA")
W, H = 2250, 1600
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
d.text((40, 20), "Wiring: cover slot → breakout board", fill=INK, font=b44)
d.text((40, 82), "6 wires. Same colour = same wire: the pad in the slot on the left goes to the hole with that colour on the right.", fill=GREY, font=f24)

# left: the slot as seen from outside, 90 px/mm
PPM, SX, SY = 90, 120, 420                          # canvas position of (u 34, v 12.5) = slot's upper-left corner seen from outside
X = lambda u: SX + (34.0 - u) * PPM
Y = lambda v: SY + (12.5 - v) * PPM
d.text((40, 200), "1. COVER, seen from outside", fill=BLUE, font=b34)
d.text((40, 246), "Close-up of the slot near the bottom edge (camera is up-left)", fill=GREY, font=f24)
d.rectangle([X(35.5), Y(14), X(23.5), Y(8)], fill=PLASTIC)
d.rounded_rectangle([X(34), Y(12.5), X(25), Y(9.5)], radius=PPM, fill=MASK)
for n, (u, v) in WIRE.items():
    s = NAME[n]; h = (0.6 if n in (1, 2, 7) else 0.5) * PPM
    box = [X(u) - h, Y(v) - h, X(u) + h, Y(v) + h]
    if n == 1:
        d.rectangle(box, fill=(120, 120, 125), outline=INK, width=2)
        d.line([box[0], box[1], box[2], box[3]], fill=RED, width=6); d.line([box[0], box[3], box[2], box[1]], fill=RED, width=6)
    else:
        d.rectangle(box, fill=COL[s], outline=INK, width=3)
        d.text((X(u), Y(v)), s, fill=TXT[s], font=b26 if len(s) < 3 else ImageFont.truetype(FB, 22), anchor="mm")
d.text((X(26.0), Y(12.5) - 50), "VIN: no wire", fill=RED, font=b26, anchor="mb")
ty = Y(8) + 30
for line, col, f in [("Upper row:  5V   SCL   ID   (VIN: no wire)", INK, b26),
                     ("Lower row:  GND   INT   SDA", INK, b26),
                     ("These are the pads on the glued-in contact board", GREY, f24),
                     ("that you see through the slot.", GREY, f24)]:
    d.text((40, ty), line, fill=col, font=f); ty += 40

# right: breakout board
BX, BY = 1000, 330
d.text((BX + 170, 200), "2. BREAKOUT BOARD", fill=BLUE, font=b34)
cv.paste(bo, (BX, BY), bo)
for s, x in HOLE_X.items():
    hx, hy = BX + x, BY + HOLE_Y
    d.ellipse([hx - 24, hy - 24, hx + 24, hy + 24], fill=COL[s], outline=INK, width=3)
d.rounded_rectangle([BX + 395, BY + 175, BX + 905, BY + 265], radius=20, outline=RED, width=6)
d.text((BX + 650, BY + 20), "WIRES FROM THE COVER: solder here", fill=RED, font=b30, anchor="mb")
d.text((BX + 650, BY + 56), "(the 6 round holes with the labels 5V … ID right below them)", fill=RED, font=f24, anchor="mb")
d.rounded_rectangle([BX + 385, BY + 582, BX + 915, BY + 664], radius=14, outline=GREY, width=5)
d.text((BX + 650, BY + 1000), "Black header = pins INTO THE BREADBOARD (→ RP2040).", fill=INK, font=b26, anchor="mb")
d.text((BX + 650, BY + 1040), "No wires from the cover here.", fill=INK, font=b26, anchor="mb")
d.text((BX + 650, BY + 1090), "If you also put pins into the wire holes: solder each wire onto that pin.", fill=GREY, font=f24, anchor="mb")
cv = cv.crop((0, 0, W, max(ty, BY + 1110) + 20)); cv.save(res); print(res, cv.size)
