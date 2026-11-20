# Pinout of the contact board's wire pads as seen from OUTSIDE the dev cover, through the wire slot.
# Once the board is glued in, its printed labels sit under the plastic (above/below the slot), so this sheet replaces them.
# Pad positions/sizes copied from pcb/contact/make_board.py (WIRE, POWER, WIRE_PAD, PWIRE_PAD); keep in sync.
# Usage (repo root): blender -b --python scripts/outside_render.py -- <dir>; python3 scripts/outside_sheet.py <dir> <result.png>
import os, sys
from PIL import Image, ImageDraw, ImageFont
src, res = sys.argv[1:3]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f22, b24, b30, b40 = ImageFont.truetype(F, 22), ImageFont.truetype(FB, 24), ImageFont.truetype(FB, 30), ImageFont.truetype(FB, 40)
RED, BLUE, INK, GREY, GOLD, MASK = (210, 30, 80), (30, 90, 200), (25, 25, 30), (110, 110, 120), (225, 180, 60), (40, 95, 60)
WIRE = {7: (32.9, 11.75), 5: (30.6, 11.75), 3: (28.3, 11.75), 1: (26.0, 11.75),
        6: (27.15, 10.25), 4: (29.45, 10.25), 2: (31.75, 10.25)}
NAME = {1: "VIN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V"}
POWER = {1, 2, 7}
SLOT_U, SLOT_V = (25.0, 34.0), (9.5, 12.5)

st = Image.open(os.path.join(src, "straight.png")).convert("RGB")
st = st.resize((st.width * 5 // 8, st.height * 5 // 8), Image.LANCZOS)        # 5 px/mm, view 84 x 166 mm at (0, -0.3)
sl = Image.open(os.path.join(src, "slot.png")).convert("RGB")                 # 60 px/mm, 18 x 9 mm at u 29.5, v 11
PPM, CU, CV = 60, 29.5, 11.0
X = lambda u: sl.width / 2 + (CU - u) * PPM        # outside view: u (from the phone's right edge) grows to the left
Y = lambda v: sl.height / 2 - (v - CV) * PPM
# the board shows through the hole: paint the hole's (white) pixels in solder-mask colour, then the pads
px = sl.load()
for x in range(int(X(SLOT_U[1])) - 2, int(X(SLOT_U[0])) + 3):
    for y in range(int(Y(SLOT_V[1])) - 2, int(Y(SLOT_V[0])) + 3):
        if 0 <= x < sl.width and 0 <= y < sl.height and min(px[x, y]) > 200: px[x, y] = MASK
ds = ImageDraw.Draw(sl)
for n, (u, v) in WIRE.items():
    h = (1.2 if n in POWER else 1.0) / 2 * PPM
    ds.rectangle([X(u) - h, Y(v) - h, X(u) + h, Y(v) + h], fill=(160, 40, 40) if n == 1 else GOLD)

# canvas: label rows above and below the close-up
TOP, GAP = 150, 120
W, H = 40 + st.width + 70 + sl.width + 40, max(150 + st.height + 60, TOP + GAP + sl.height + GAP + 260)
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
d.text((40, 20), "Wire pads seen from OUTSIDE, through the slot", fill=INK, font=b40)
d.text((40, 78), "The board's own labels are under the plastic once it's glued in. Positions from pcb/contact/make_board.py.", fill=GREY, font=f22)
# left: whole back for orientation
OX, OY = 40, 150
cv.paste(st, (OX, OY))
d.text((OX, OY - 40), "Whole back (camera top left)", fill=BLUE, font=b24)
sx = lambda u: OX + st.width / 2 + (37.0 - u) * 5
sy = lambda v: OY + st.height / 2 - (-78.8 + v + 0.3) * 5
d.rectangle([sx(SLOT_U[1]) - 8, sy(SLOT_V[1]) - 8, sx(SLOT_U[0]) + 8, sy(SLOT_V[0]) + 8], outline=RED, width=4)
# right: close-up
QX, QY = OX + st.width + 70, TOP + GAP
cv.paste(sl, (QX, QY))
d.text((QX, TOP - 40), "Close-up of the slot (×12, same orientation)", fill=BLUE, font=b24)
d.line([(sx(SLOT_U[0]) + 10, sy(SLOT_V[1]) - 8), (QX - 6, QY + sl.height / 2)], fill=RED, width=3)
for n, (u, v) in WIRE.items():
    x, y = QX + X(u), QY + Y(v)
    top = v > 11
    ly = QY - 50 if top else QY + sl.height + 50
    col = RED if n == 1 else INK
    d.line([(x, y + (-35 if top else 35)), (x, ly + (20 if top else -20))], fill=col, width=3)
    d.text((x, ly), NAME[n], fill=col, font=b30, anchor="mb" if top else "mt")
    d.text((x, ly + (-38 if top else 38)), "pin %d" % n, fill=GREY, font=f22, anchor="mb" if top else "mt")
y = QY + sl.height + GAP + 30
for line, col in [("Top row, left to right:      5V   SCL   ID   VIN", INK),
                  ("Bottom row, left to right:  GND   INT   SDA", INK),
                  ("VIN (pin 1, red): leave unconnected on the dev cover.", RED),
                  ("Big pads (1.2 mm) = power: 5V, GND, VIN. Small (1.0 mm) = signals.", INK),
                  ("Board colour drawn green; yours may differ.", GREY)]:
    d.text((QX, y), line, fill=col, font=b24 if col == RED else f22); y += 36
cv = cv.crop((0, 0, W, max(y, OY + st.height) + 30)); cv.save(res); print(res, cv.size)
