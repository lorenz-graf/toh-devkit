# Overview image of the dev cover model (make_dev_cover.py): inside close-up with the indent, pads and wire slot,
# plus the outside. Renders (measure_render.py on model/ctohm-dev.stl):
#   inside close-up: -- <stl> <in.png> -17.5 -71.8 32 45 20 ; outside: -- <stl> <out.png> 0 -0.3 8 84 166 outside
# Usage: python3 dev_cover_sheet.py <in.png> <out.png> <result.png>
import sys
from PIL import Image, ImageDraw, ImageFont
fin, fout, res = sys.argv[1:4]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f22, f26 = ImageFont.truetype(F, 22), ImageFont.truetype(F, 26)
b26, b30, b40 = (ImageFont.truetype(FB, s) for s in (26, 30, 40))
RED, BLUE, INK, GREY, GREEN, GOLD = (210, 30, 80), (30, 90, 200), (25, 25, 30), (110, 110, 120), (20, 140, 60), (235, 190, 60)
ii, oo = Image.open(fin).convert("RGB"), Image.open(fout).convert("RGB")
oo = oo.resize((oo.width * 3 // 4, oo.height * 3 // 4), Image.LANCZOS)   # 6 px/mm
W, H = 60 + oo.width + 60 + ii.width + 40, 1400
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
d.text((40, 20), "Dev cover: cTOH-M frame + wire slot (model/ctohm-dev.step|stl)", fill=INK, font=b40)
d.text((40, 80), "The contact-board indent (0.6 mm deep, pad dimples) is part of cTOH-M already; new is only the wire slot through its floor.", fill=GREY, font=f22)
# outside
OX1, OY1 = 40, 200
cv.paste(oo, (OX1, OY1))
d.text((OX1, OY1 - 56), "OUTSIDE\n(seen from behind)", fill=BLUE, font=b26)
# slot on the outside: render 8 px/mm scaled 0.75 -> 6 px/mm, centre (0,-0.3), outside view mirrors X
ox = lambda u: OX1 + oo.width / 2 + (37.0 - u) * 6       # u from the right edge -> right side of the image
oy = lambda v: OY1 + oo.height / 2 - (-78.8 + v + 0.3) * 6
d.rectangle([ox(34) - 6, oy(12.5) - 6, ox(25) + 6, oy(9.5) + 6], outline=RED, width=4)
d.text((ox(29.5), oy(12.5) - 14), "wire slot", fill=RED, font=b26, anchor="mb")
d.text((OX1, OY1 + oo.height + 10), "Print this face down on the bed.\nCamera bump: separate part, as before.", fill=INK, font=f22)
# inside close-up
OX2, OY2 = OX1 + oo.width + 60, 200
cv.paste(ii, (OX2, OY2))
d.text((OX2, OY2 - 40), "INSIDE, connector corner (looking into the cover, side wall left)", fill=BLUE, font=b26)
X = lambda u: OX2 + ii.width / 2 + (u - 19.5) * 32
Y = lambda v: OY2 + ii.height / 2 - (v - 7) * 32
PINS = {1: (19.8, 8.45), 2: (19.8, 5.55), 3: (16.9, 8.45), 4: (16.9, 5.55), 5: (14.0, 8.45), 6: (14.0, 5.55), 7: (11.1, 8.45)}
SIG = {1: "5V-IN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V-OUT"}
for n, (u, v) in PINS.items():
    r = 1.15 * 32
    d.ellipse([X(u) - r, Y(v) - r, X(u) + r, Y(v) + r], outline=GOLD, width=4)
    d.text((X(u), Y(v)), str(n), fill=INK, font=b26, anchor="mm")
# PCB outline = indent minus 0.2 mm
c = 0.2
L = [(36.4 - c, 14.5 - c), (36.4 - c, 7.35 + c), (21.6 - c, 7.35 + c), (21.6 - c, 3.65 + c), (8.9 + c, 3.65 + c), (8.9 + c, 14.5 - c)]
d.line([(X(u), Y(v)) for u, v in L + L[:1]], fill=GREEN, width=3)
d.text((X(9.4), Y(13.9)), "PCB outline (0.6 mm board, 0.2 mm clearance)", fill=GREEN, font=b26, anchor="la")
d.text((X(29.5), Y(11)), "wire slot\n9 × 3 mm, through", fill=RED, font=b26, anchor="mm", align="center")
def dim(p, q, txt, col=GREY, side=-1):
    import math
    d.line([p, q], fill=col, width=2)
    for a, b in ((p, q), (q, p)):
        g = math.atan2(a[1] - b[1], a[0] - b[0])
        d.polygon([a, (a[0] - 12 * math.cos(g - 0.4), a[1] - 12 * math.sin(g - 0.4)), (a[0] - 12 * math.cos(g + 0.4), a[1] - 12 * math.sin(g + 0.4))], fill=col)
    d.text(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + side * 6), txt, fill=col, font=b26, anchor="mb" if side < 0 else "mt")
dim((X(8.9), Y(15.6)), (X(36.4), Y(15.6)), "indent 27.5")
dim((X(25), Y(8.7)), (X(34), Y(8.7)), "9.0", col=RED, side=1)
y = OY2 + ii.height + 20
for line in ["Pads (gold rings): 2.3 mm, where Jolla's Inari has them; cTOH-M's dimples sit at the same spots.",
             "Board: 0.6 mm thick → pads flush with the inner surface, like the Inari (S = 0).",
             "Wires: soldered to pads on the board's BACK side over the slot, out through the slot",
             "to the breadboard on the outside. Slot sits under the board's right arm, away from the pins.",
             "Floor under the indent: 0.8 mm; plate elsewhere 1.4 mm."]:
    d.text((OX2, y), line, fill=INK, font=f22); y += 32
for n in (1, 2): pass
cv = cv.crop((0, 0, W, max(y, OY1 + oo.height + 70) + 10)); cv.save(res); print(res, cv.size)
