# Check image for the contact PCB: KiCad renders of both sides + the board drawn into the dev cover
# (inside close-up from measure_render.py: -- ctohm-dev.stl <in.png> -17.5 -71.8 32 45 20).
# Usage: python3 pcb_check_sheet.py <pcb_top.png> <pcb_bottom.png> <cover_in.png> <out.png>
# Geometry must match ../pcb/contact/make_board.py.
import sys
from PIL import Image, ImageDraw, ImageFont
ft, fb, fc, out = sys.argv[1:5]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f22 = ImageFont.truetype(F, 22); b20, b26, b30, b40 = (ImageFont.truetype(FB, s) for s in (20, 26, 30, 40))
RED, BLUE, INK, GREY, GREEN, GOLD = (210, 30, 80), (30, 90, 200), (25, 25, 30), (110, 110, 120), (20, 140, 60), (235, 190, 60)
crop = (420, 240, 1340, 620)
top, bot = Image.open(ft).convert("RGB").crop(crop), Image.open(fb).convert("RGB").crop(crop)
cov = Image.open(fc).convert("RGB")
W = 40 + top.width + 40 + bot.width + 40
H = 130 + top.height + 110 + cov.height + 260
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
d.text((40, 20), "TOH DevKit contact board v2: 0.6 mm, ENIG, 1 A on VIN/GND/5V", fill=INK, font=b40)
d.text((40, 76), "KiCad renders. Board ≈ 27.1 × 10.45 mm, L-shape = cTOH-M indent minus 0.2 mm.", fill=GREY, font=f22)
y0 = 130
cv.paste(top, (40, y0 + 40)); cv.paste(bot, (40 + top.width + 40, y0 + 40))
d.text((40, y0), "COVER SIDE (top): seen from outside / from behind the phone", fill=BLUE, font=b26)
d.text((40 + top.width + 40, y0), "PHONE SIDE (bottom): what the pins touch", fill=RED, font=b26)
# cover overlay (inside view = phone side)
y1 = y0 + 40 + top.height + 70
d.text((40, y1 - 44), "In the cover (looking into it, side wall left): board, pads, vias, wire pads over the slot", fill=INK, font=b26)
OX, OY = 40, y1
cv.paste(cov, (OX, OY))
X = lambda u: OX + cov.width / 2 + (u - 19.5) * 32
Y = lambda v: OY + cov.height / 2 - (v - 7) * 32
OUTLINE = [(9.1, 3.85), (21.4, 3.85), (21.4, 7.55), (36.2, 7.55), (36.2, 14.3), (9.1, 14.3)]
PINS = {1: (19.8, 8.45), 2: (19.8, 5.55), 3: (16.9, 8.45), 4: (16.9, 5.55), 5: (14.0, 8.45), 6: (14.0, 5.55), 7: (11.1, 8.45)}
VIA = {5: (14.0, 10.4), 3: (16.9, 10.4), 6: (12.55, 7.0), 4: (15.45, 7.0), 2: (18.35, 7.0)}
LANE = {5: 13.5, 3: 13.1, 6: 9.2, 4: 8.75, 2: 8.1}
BLANE = {7: 13.4, 1: 12.4}; BVIA = {7: (34.1, 11.75), 1: (24.9, 11.75)}; POWER = {1, 2, 7}
WIRE = {7: (32.9, 11.75), 5: (30.6, 11.75), 3: (28.3, 11.75), 1: (26.0, 11.75), 6: (27.15, 10.25), 4: (29.45, 10.25), 2: (31.75, 10.25)}
SIG = {1: "VIN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V"}
d.polygon([(X(u), Y(v)) for u, v in OUTLINE], outline=GREEN, width=4)
for n in VIA:    # signals + GND on the cover side (dim); power drawn thicker
    (vu, vv), (wu, wv) = VIA[n], WIRE[n]; w = 8 if n in POWER else 3
    d.line([(X(vu), Y(vv)), (X(vu), Y(LANE[n])), (X(wu), Y(LANE[n])), (X(wu), Y(wv))], fill=(150, 150, 120), width=w)
    d.line([(X(PINS[n][0]), Y(PINS[n][1])), (X(vu), Y(vv))], fill=(150, 150, 120), width=w)
for n in BVIA:   # VIN, 5V on the phone side (orange, thick)
    (pu, pv), (vu, vv), y = PINS[n], BVIA[n], BLANE[n]
    d.line([(X(pu), Y(pv)), (X(pu), Y(y)), (X(vu), Y(y)), (X(vu), Y(vv)), (X(WIRE[n][0]), Y(WIRE[n][1]))], fill=(230, 140, 40), width=8)
for n, (u, v) in WIRE.items():
    h = 19 if n in POWER else 16
    d.rectangle([X(u) - h, Y(v) - h, X(u) + h, Y(v) + h], outline=BLUE, width=3)
    d.text((X(u), Y(v) + (-22 if v > 11 else 22)), SIG[n], fill=BLUE, font=b20, anchor="mb" if v > 11 else "mt")
for n, (u, v) in PINS.items():
    r = 1.15 * 32
    d.ellipse([X(u) - r, Y(v) - r, X(u) + r, Y(v) + r], fill=GOLD, outline=INK, width=2)
    d.text((X(u), Y(v) - 6), str(n), fill=INK, font=b26, anchor="mm"); d.text((X(u), Y(v) + 16), SIG[n], fill=INK, font=b20, anchor="mm")
for n, (u, v) in list(VIA.items()) + list(BVIA.items()):
    d.ellipse([X(u) - 10, Y(v) - 10, X(u) + 10, Y(v) + 10], fill=(200, 200, 200), outline=INK, width=2)
y = OY + cov.height + 20
for t in ["Gold = contact pads (phone side, 2.3 mm, at the pin positions). Grey dots = vias. Dim lines = traces on the cover side,",
          "orange = VIN and 5V on the phone side. Power (VIN, GND, 5V) 0.5 mm wide and 1.2 mm wire pads: 1 A, e.g. a battery cover via pin 1.",
          "Blue squares = wire pads (1 mm, cover side) over the slot; wires go from them through the slot to the outside.",
          "Labels on the board are on the cover side, so you read them from the outside through the slot.",
          "VIN (pin 1): leave unconnected on the dev cover; for battery covers (chonk) it carries up to 1 A into the phone.",
          "Order: JLCPCB, 2 layers, 0.6 mm, ENIG, vias tented. Design check (DRC): 0 errors."]:
    d.text((40, y), t, fill=INK, font=f22); y += 34
cv.crop((0, 0, W, y + 20)).save(out); print(out)
