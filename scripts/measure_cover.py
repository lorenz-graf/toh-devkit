# Measuring sheet for the pad placement on a finished back cover (Inari Blue), using the notches
# of the two clips next to the connector as reference.
# Base: blender -b --python measure_render.py -- <toh-3d-model.stl> <zoom.png> -17.5 -71.8 32 45 20
# (inside of the cover, connector corner, 32 px/mm, centre u=19.5 v=7). Then:
# python3 measure_cover.py <zoom.png> <out.png>
# Notch edges and pad positions: Jolla's cover model (toh-3d-model.step) and JP2601 back drawing.
import sys
from PIL import Image, ImageDraw, ImageFont
base, out = sys.argv[1:3]
F = "/usr/share/fonts/TTF/DejaVuSans.ttf"; FB = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
f22, f26 = ImageFont.truetype(F, 22), ImageFont.truetype(F, 26)
b26, b30, b40 = (ImageFont.truetype(FB, s) for s in (26, 30, 40))
RED, BLUE, INK, GREY, GOLD = (210, 30, 80), (30, 90, 200), (25, 25, 30), (110, 110, 120), (235, 190, 60)
img = Image.open(base).convert("RGB")
OX, OY = 40, 150
W, H = OX + img.width + 40, OY + img.height + 560
cv = Image.new("RGB", (W, H), "white"); cv.paste(img, (OX, OY)); d = ImageDraw.Draw(cv)
PPM, UC, VC = 32, 19.5, 7                  # px/mm and view centre (phone coords) of the base render
X = lambda u: OX + img.width / 2 + (u - UC) * PPM     # inside view: side wall left, bottom wall down
Y = lambda v: OY + img.height / 2 - (v - VC) * PPM

def arrow(p, q, col=RED, w=4, hs=14):
    import math
    d.line([p, q], fill=col, width=w)
    for a, b in ((p, q), (q, p)):
        g = math.atan2(a[1] - b[1], a[0] - b[0])
        d.polygon([a, (a[0] - hs * math.cos(g - 0.4), a[1] - hs * math.sin(g - 0.4)),
                      (a[0] - hs * math.cos(g + 0.4), a[1] - hs * math.sin(g + 0.4))], fill=col)
def tag(c, t, r=26):
    d.ellipse([c[0] - r - 4, c[1] - r - 4, c[0] + r + 4, c[1] + r + 4], fill=(255, 220, 0))
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=RED)
    d.text(c, t, fill="white", font=b30 if len(t) == 1 else b26 if r > 22 else f22, anchor="mm")

d.text((OX, 20), "BACK COVER (Inari Blue): pad position from the two clips", fill=INK, font=b40)
d.text((OX, 80), "Looking into the cover, connector corner. Side wall left, bottom wall at the bottom. Shape from Jolla's cover model;\npads drawn where the phone's pins are. Measure on the real cover with the caliper.", fill=GREY, font=f22)

# bottom clip (cover model): u 11.3..15.1, lower side v 1.65, upper side v 2.44
CU0, CU1, CLO, CUP = 11.3, 15.1, 1.65, 2.44
d.rectangle([X(CU0), Y(CUP), X(CU1), Y(CLO)], outline=BLUE, width=4)
d.text((X(13.2), Y(-1.0)), "bottom clip", fill=BLUE, font=b26, anchor="mt")
d.line([(X(13.2), Y(-0.9)), (X(13.2), Y(CLO))], fill=BLUE, width=2)

PINS = {1: (19.8, 8.45), 2: (19.8, 5.55), 3: (16.9, 8.45), 4: (16.9, 5.55), 5: (14.0, 8.45), 6: (14.0, 5.55), 7: (11.1, 8.45)}
for n, (u, v) in PINS.items():
    r = 1.15 * PPM   # pads 2.3 mm (measured on the Inari Blue)
    d.ellipse([X(u) - r, Y(v) - r, X(u) + r, Y(v) + r], fill=GOLD, outline=INK, width=3)
    d.text((X(u), Y(v)), str(n), fill=INK, font=b30, anchor="mm")
SIG = {1: "5V-IN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V-OUT"}   # as printed on the Inari's board
for n, (u, v) in PINS.items():
    d.text((X(u), Y(v + (1.55 if v > 7 else -1.55))), SIG[n], fill=INK, font=f22, anchor="mb" if v > 7 else "mt")
d.ellipse([X(14) - 5, Y(5.55) - 5, X(14) + 5, Y(5.55) + 5], fill=RED)   # pin 6 centre

RC0, RC1, RV0, RV1 = 37.95, 38.95, 9.1, 12.4
d.rectangle([X(RC0), Y(RV1), X(RC1), Y(RV0)], outline=BLUE, width=4)
d.text((X(38.45), Y(13.4)), "right clip", fill=BLUE, font=b26, anchor="mb")
d.text((X(16.5), Y(15.6)), "indent for the contact board", fill=GREY, font=f22, anchor="mm")
def done(c, t, r=26):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill="white", outline=GREY, width=3)
    d.text(c, t, fill=GREY, font=b30 if len(t) == 1 else b26 if r > 22 else f22, anchor="mm")
# Y: clip upper / lower side -> pin 6 centre (straight up), measured 3.0 / 3.8
d.line([(X(14), Y(5.55)), (X(9.6), Y(5.55))], fill=GREY, width=2)
arrow((X(10.6), Y(CUP)), (X(10.6), Y(5.55)), col=GREY, w=3); d.line([(X(CU0), Y(CUP)), (X(10.3), Y(CUP))], fill=GREY, width=2)
arrow((X(9.9), Y(CLO)), (X(9.9), Y(5.55)), col=GREY, w=3); d.line([(X(CU0), Y(CLO)), (X(9.6), Y(CLO))], fill=GREY, width=2)
d.text((X(10.6) + 8, Y(4.0)), "3.0", fill=BLUE, font=b26, anchor="lm")
d.text((X(9.9) - 8, Y(3.6)), "3.8", fill=BLUE, font=b26, anchor="rm")
done((X(7.0), Y(5.6)), "Y")
# R1: pin 1 centre -> right clip, left side 18.0 / right side 19.0 (measured)
d.line([(X(19.8), Y(8.45) + PPM), (X(19.8), Y(3.0))], fill=GREY, width=2)
for uu, vv, txt in ((RC0, 4.6, "18.0"), (RC1, 3.4, "19.0")):
    d.line([(X(uu), Y(RV0)), (X(uu), Y(vv - 0.4))], fill=GREY, width=2)
    arrow((X(19.8), Y(vv)), (X(uu), Y(vv)), col=GREY, w=3)
    d.text(((X(19.8) + X(uu)) / 2, Y(vv) - 6), txt, fill=BLUE, font=b26, anchor="mb")
done((X(29), Y(6.2)), "P1")
# PP: row of 4, outer edge of pad 7 -> outer edge of pad 1 = 11.0; pad width 2.3 (measured)
e0, e1 = 11.1 - 1.15, 19.8 + 1.15
for e in (e0, e1):
    d.line([(X(e), Y(8.45)), (X(e), Y(11.0))], fill=GREY, width=2)
arrow((X(e0), Y(10.6)), (X(e1), Y(10.6)), col=GREY, w=3)
d.text(((X(e0) + X(e1)) / 2, Y(10.6) - 6), "11.0", fill=BLUE, font=b26, anchor="mb")
d.line([(X(11.1 - 1.15), Y(8.45)), (X(11.1 - 1.15), Y(9.9))], fill=GREY, width=2)
arrow((X(11.1 - 1.15), Y(9.75)), (X(11.1 + 1.15), Y(9.75)), col=GREY, w=2, hs=8)
d.text((X(11.1 - 1.15) - 6, Y(9.75)), "2.3", fill=BLUE, font=b26, anchor="rm")
done((X(22.6), Y(10.6)), "PP")


# table
y = OY + img.height + 40
rows = [("Y", "bottom clip upper / lower side → pad 6 centre", "3.1 / 3.9", "measured 3.0 / 3.8: done"),
        ("P1", "pad 1 centre → right clip left / right side", "18.15 / 19.15", "measured 18.0 / 19.0: done"),
        ("PP", "row of 4 outer edges / pad width", "8.7 + pad", "measured 11.0 / 2.3 → pitch 2.90: done"),
        ("S", "pad surface height above the cover's inner surface", "", "measured 0 (flush): done")]
d.text((OX + 70, y), "what", fill=GREY, font=f22); d.text((OX + 780, y), "model", fill=GREY, font=f22); d.text((OX + 1010, y), "how", fill=GREY, font=f22)
y += 40
for k, what, exp, how in rows:
    (done if k in ("Y", "P1", "PP", "S") else tag)((OX + 30, y + 14), k, r=20)
    d.text((OX + 70, y), what, fill=INK, font=f26)
    d.text((OX + 780, y), exp, fill=INK, font=b26)
    d.text((OX + 1010, y), how, fill=GREY, font=f22)
    y += 56
d.text((OX, y + 10), "Pad 6 = row of 3, the pad nearest the side wall (it sits straight above the bottom clip).", fill=INK, font=f22)
# S: cross-section, board sunk into the indent, pads flush with the inner surface
sy = y + 110
d.text((OX, sy - 50), "S = 0: cross-section through the pads (sketch, not to scale), cover inside facing up", fill=INK, font=b26)
x0 = OX + 40; top = sy + 60
d.rectangle([x0, top, x0 + 300, top + 50], fill=(120, 150, 200), outline=INK, width=2)
d.rectangle([x0 + 640, top, x0 + 940, top + 50], fill=(120, 150, 200), outline=INK, width=2)
d.rectangle([x0 + 300, top + 34, x0 + 640, top + 50], fill=(120, 150, 200), outline=INK, width=2)   # thin floor under the indent
d.rectangle([x0 + 300, top + 8, x0 + 640, top + 34], fill=(60, 120, 70), outline=INK, width=2)     # board
for k in range(4):
    xx = x0 + 340 + k * 80
    d.rectangle([xx, top, xx + 50, top + 8], fill=GOLD, outline=INK, width=2)
d.line([(x0 - 30, top), (x0 + 980, top)], fill=RED, width=2)
d.text((x0 + 990, top), "pads flush with the\ninner surface (S = 0)", fill=RED, font=f22, anchor="lm")
d.text((x0 + 470, top + 21), "contact board", fill="white", font=f22, anchor="mm")
d.text((x0 + 10, top + 58), "cover", fill=GREY, font=f22); d.text((x0 + 470, top + 58), "indent", fill=GREY, font=f22, anchor="mt")
y = top + 100
cv = cv.crop((0, 0, W, y + 20)); cv.save(out); print(out, cv.size)
