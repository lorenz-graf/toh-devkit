# Generates dev-toh-breakout.kicad_pcb: small board on the breadboard side of the dev cover.
# The 6 wires from the cover slot (contact board wire pads, VIN not used) are soldered into the top row;
# a 6-pin 2.54 mm header plugs into the breadboard. On board: D1 1N5817 in the phone's 5 V line (stops USB
# backfeed into the phone when the MCU is also on USB), ID mode selector: JP2 connects ID to R1 6.2 kOhm (DEV mode,
# dev ID, bridged by default) or R2 10 kOhm (CHIP mode, RP2040 emulates the memory chip), see ID-modes.md in the repo root; JP1 INT -> GND
# (bridged by default = "cover attached"; cut it if the MCU should drive INT later). J3 "5V MEAS": 2-pin header in the
# 5 V line, with JP4 (bridged solder jumper) in parallel so 5 V works out of the box; to measure, cut JP4 once and
# use J3 (jumper cap / Dupont bridge for normal use, ammeter to measure the draw). JP3: D1 bypass (open; bridge only
# when the RP2040 is NOT on USB, gives modules the full 5 V).
# v3: every THT part has an SMD footprint in parallel (D1S SMA, e.g. SS14 (standard SMA pads: the hand-solder ones
# overlap D1's holes and leave no room for the band); R1S/R2S 1206, 0805 also fits by hand),
# sitting between the THT holes under the THT body. Fit either the THT part or the SMD part.
# Run: python3 make_board.py   (KiCad 10 pcbnew module). Coordinates in mm, board origin = top-left at (100, 100).
import pcbnew, json
from pcbnew import FromMM as mm, ToMM, VECTOR2I

STD = "/usr/share/kicad/footprints"
OUT = "dev-toh-breakout.kicad_pcb"
W, H = 31.0, 23.6
P = lambda x, y: VECTOR2I(mm(100 + x), mm(100 + y))
COLS = ["5V", "GND", "SDA", "SCL", "INT", "ID"]          # wire holes and header pins, left to right
X0, PITCH, Y_WIRE, Y_HDR = 8.0, 2.54, 2.5, 14.5
X = {s: X0 + i * PITCH for i, s in enumerate(COLS)}
NETS = ["5V_PHONE", "5V_D", "5V", "GND", "SDA", "SCL", "INT", "ID", "ID_A", "ID_B"]
TRACK, BUS_Y = 0.4, 19.7

b = pcbnew.BOARD()
ds = b.GetDesignSettings(); ds.SetBoardThickness(mm(1.6))
net = {}
for n in NETS:
    ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); net[n] = ni

for (x1, y1), (x2, y2) in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]:
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetWidth(mm(0.1)); b.Add(s)

def place(lib, name, ref, x, y, want):
    """Place a footprint so that pad '2' lies in direction `want` ('right' or 'up' or 'down') from pad '1'."""
    for rot in (0, 90, 180, 270):
        fp = pcbnew.FootprintLoad(f"{STD}/{lib}.pretty", name)
        fp.SetReference(ref); fp.SetOrientationDegrees(rot); fp.SetPosition(P(x, y))
        pads = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
        d = pads["2"] - pads["1"]
        ok = {"right": d.x > 0 and d.y == 0, "up": d.y < 0 and d.x == 0, "down": d.y > 0 and d.x == 0}[want]
        if ok:
            fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
            b.Add(fp); return fp
    raise RuntimeError(name)

def pad(fp, num):
    p = [q for q in fp.Pads() if q.GetNumber() == str(num)][0]; return p
def at(fp, num):
    v = pad(fp, num).GetPosition(); return (ToMM(v.x) - 100, ToMM(v.y) - 100)

jw = place("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical", "J1", X["5V"], Y_WIRE, "right")
jw.Models().clear()                     # wire holes: no header gets soldered here
for g in list(jw.GraphicalItems()):     # and no header outline on the silkscreen (makes room for the DEV label)
    if g.GetLayer() == pcbnew.F_SilkS: jw.Remove(g)
jh = place("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical", "J2", X["5V"], Y_HDR, "right")
# DO-41: pad 1 = cathode (band). Anode (2) up toward the wire, cathode (1) down toward the header.
d1 = place("Diode_THT", "D_DO-41_SOD81_P10.16mm_Horizontal", "D1", 3.5, 14.16, "up")
r1 = place("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "R1", 24.4, 4.0, "down")   # 6.2k, DEV mode
r2 = place("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "R2", 27.8, 4.0, "down")   # 10k, CHIP mode
# SMD alternatives, centred between the THT holes (same nets, same orientation: D1S cathode toward the header)
YC = 14.16 - 5.08
d1s = place("Diode_SMD", "D_SMA", "D1S", 3.5, YC, "up")
r1s = place("Resistor_SMD", "R_1206_3216Metric_Pad1.30x1.75mm_HandSolder", "R1S", 24.4, YC, "down")
r2s = place("Resistor_SMD", "R_1206_3216Metric_Pad1.30x1.75mm_HandSolder", "R2S", 27.8, YC, "down")
for fp in (d1s, r1s, r2s):              # the THT outline (with the diode band) is the silkscreen for both
    gi = fp.GraphicalItems(); items = [g for g in gi]   # keep the proxy alive while iterating (SWIG)
    for g in items:
        # no courtyard (overlapping D1/R1/R2 is intended), no own silk. Moved to F.Fab instead of removed:
        # Remove() + SWIG ownership breaks the pcbnew bindings later in the script
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.F_SilkS): g.SetLayer(pcbnew.F_Fab)
# D1's silk body + band would sit on D1S's pads (and be clipped away): replace it by two side lines and a band
# beside the pads (cathode end, toward the header), so the polarity stays visible with either part fitted
gi = d1.GraphicalItems()
for g in [g for g in gi]:
    if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() == "PCB_SHAPE" and g.GetBoundingBox().Intersects(d1s.GetBoundingBox()):
        g.SetLayer(pcbnew.F_Fab)
def silk_line(x1, y1, x2, y2, w=0.15):
    l = pcbnew.PCB_SHAPE(b); l.SetShape(pcbnew.SHAPE_T_SEGMENT); l.SetLayer(pcbnew.F_SilkS)
    l.SetStart(P(x1, y1)); l.SetEnd(P(x2, y2)); l.SetWidth(mm(w)); b.Add(l)
padhalf = ToMM(pad(d1s, 1).GetBoundingBox().GetWidth()) / 2 + 0.25
k_bot = ToMM(pad(d1s, 1).GetBoundingBox().GetBottom()) - 100           # lower edge of D1S's cathode pad
k_tht = ToMM(pad(d1, 1).GetBoundingBox().GetTop()) - 100               # upper edge of D1's cathode pad
band_y = (k_bot + k_tht) / 2                                            # band in the gap between the two
a_top = ToMM(pad(d1, 2).GetBoundingBox().GetBottom()) - 100 + 0.3     # below D1's anode pad
for sx in (-1, 1):
    silk_line(3.5 + sx * padhalf, a_top, 3.5 + sx * padhalf, band_y)
silk_line(3.5 - padhalf, band_y, 3.5 + padhalf, band_y, min(0.5, k_tht - k_bot - 0.35))   # band = cathode side
j2 = place("Jumper", "SolderJumper-3_P1.3mm_Bridged12_Pad1.0x1.5mm", "JP2", 26.1, 1.6, "right")     # 1-2 bridged = DEV mode
sj = place("Jumper", "SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm", "JP1", X["INT"], 18.2, "down")
jm = place("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical", "J3", 3.5, 18.4, "right")   # 5V MEAS
jb = place("Jumper", "SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm", "JP3", 6.5, 9.1, "down")               # D1 bypass
jp4 = place("Jumper", "SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm", "JP4", 4.77, 21.8, "right")       # parallel to J3

for i, s in enumerate(COLS, 1):
    pad(jw, i).SetNet(net["5V_PHONE" if s == "5V" else s]); pad(jh, i).SetNet(net[s])
pad(d1, 2).SetNet(net["5V_PHONE"]); pad(d1, 1).SetNet(net["5V_D"])
pad(jm, 1).SetNet(net["5V_D"]); pad(jm, 2).SetNet(net["5V"])
pad(jb, 1).SetNet(net["5V_PHONE"]); pad(jb, 2).SetNet(net["5V_D"])
pad(jp4, 1).SetNet(net["5V_D"]); pad(jp4, 2).SetNet(net["5V"])
pad(r1, 1).SetNet(net["ID_A"]); pad(r1, 2).SetNet(net["GND"])
pad(r2, 1).SetNet(net["ID_B"]); pad(r2, 2).SetNet(net["GND"])
pad(j2, 1).SetNet(net["ID_A"]); pad(j2, 2).SetNet(net["ID"]); pad(j2, 3).SetNet(net["ID_B"])
pad(sj, 1).SetNet(net["INT"]); pad(sj, 2).SetNet(net["GND"])
pad(d1s, 2).SetNet(net["5V_PHONE"]); pad(d1s, 1).SetNet(net["5V_D"])
pad(r1s, 1).SetNet(net["ID_A"]); pad(r1s, 2).SetNet(net["GND"])
pad(r2s, 1).SetNet(net["ID_B"]); pad(r2s, 2).SetNet(net["GND"])

def track(layer, pts, n):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetLayer(layer); t.SetWidth(mm(TRACK)); t.SetNet(net[n])
        t.SetStart(P(*a)); t.SetEnd(P(*c)); b.Add(t)

for s in ["GND", "SDA", "SCL", "INT", "ID"]:                       # straight down on the bottom layer
    track(pcbnew.B_Cu, [(X[s], Y_WIRE), (X[s], Y_HDR)], s)
a, k = at(d1, 2), at(d1, 1)
track(pcbnew.F_Cu, [(X["5V"], Y_WIRE), (a[0], Y_WIRE), a], "5V_PHONE")     # wire -> diode anode
m1, m2 = at(jm, 1), at(jm, 2); b1, b2 = at(jb, 1), at(jb, 2)
track(pcbnew.F_Cu, [k, m1], "5V_D")                                         # cathode -> J3 pin 1
track(pcbnew.F_Cu, [m2, (X["5V"], m2[1]), (X["5V"], Y_HDR)], "5V")          # J3 pin 2 -> header 5V
track(pcbnew.F_Cu, [(b1[0], Y_WIRE), b1], "5V_PHONE")                        # bypass: anode side
track(pcbnew.F_Cu, [b2, (b2[0], 15.7), (k[0], 15.7)], "5V_D")                # bypass: cathode side
p1, p2 = at(jp4, 1), at(jp4, 2)
track(pcbnew.F_Cu, [m1, (m1[0], p1[1]), p1], "5V_D")                        # JP4 in parallel to J3
track(pcbnew.F_Cu, [p2, (m2[0], p2[1]), m2], "5V")
r_a, r_b = at(r1, 1), at(r1, 2)
r2_a, r2_b = at(r2, 1), at(r2, 2)
j_1, j_2, j_3 = at(j2, 1), at(j2, 2), at(j2, 3)
# ID wire -> (bottom layer) -> via -> JP2 middle pad; JP2 outer pads -> R1 (A) / R2 (B)
VIA_ID = (j_2[0], 2.9)
track(pcbnew.B_Cu, [(X["ID"], Y_WIRE), (VIA_ID[0], Y_WIRE), VIA_ID], "ID")
v = pcbnew.PCB_VIA(b); v.SetPosition(P(*VIA_ID)); v.SetDrill(mm(0.3)); v.SetWidth(mm(0.6)); v.SetNet(net["ID"]); b.Add(v)
track(pcbnew.F_Cu, [j_2, VIA_ID], "ID")
track(pcbnew.F_Cu, [j_1, r_a], "ID_A")
track(pcbnew.F_Cu, [j_3, r2_a], "ID_B")
track(pcbnew.F_Cu, [r_b, (r_b[0], BUS_Y), (X["GND"], BUS_Y), (X["GND"], Y_HDR)], "GND")   # R1 -> GND bus -> header GND
track(pcbnew.F_Cu, [r2_b, (r2_b[0], BUS_Y), (r_b[0], BUS_Y)], "GND")                      # R2 -> GND bus
for tht, smd, n1, n2 in [(d1, d1s, "5V_D", "5V_PHONE"), (r1, r1s, "ID_A", "GND"), (r2, r2s, "ID_B", "GND")]:
    track(pcbnew.F_Cu, [at(tht, 1), at(smd, 1)], n1)                      # SMD pads in parallel to the THT pads
    track(pcbnew.F_Cu, [at(tht, 2), at(smd, 2)], n2)
s1, s2 = at(sj, 1), at(sj, 2)
track(pcbnew.F_Cu, [(X["INT"], Y_HDR), s1], "INT")
track(pcbnew.F_Cu, [s2, (s2[0], BUS_Y)], "GND")

def text(s, x, y, size=0.8, rot=0):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(P(x, y))
    t.SetTextSize(VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.15)); t.SetTextAngleDegrees(rot); b.Add(t)
for s in COLS:
    text(s, X[s], 5.6, rot=90)                 # under the wire holes
    text(s, X[s], 11.5, rot=90)                # above the header pins
text("1N5817/SS14", 1.1, 8.4, 0.8, 90)
text("DEV 6.2k", 22.35, 9.1, 0.8, 90)
text("CHIP 10k", 30.05, 9.1, 0.8, 90)
text("DEV", 22.9, 1.6, 0.7); text("CHIP", 29.5, 1.6, 0.7)
text("INT-GND", 14.4, 18.1, 0.7)
text("TOH breakout v3", 14.35, 8.3, 0.8)
text("5V MEAS", 9.3, 21.8, 0.7)
text("NO USB", 6.5, 5.6, 0.7, 90)

pcbnew.SaveBoard(OUT, b)
json.dump({"meta": {"filename": OUT.replace(".kicad_pcb", ".kicad_pro"), "version": 1},
           "board": {"design_settings": {"rules": {
               "min_clearance": 0.15, "min_copper_edge_clearance": 0.3, "min_track_width": 0.15,
               "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3,
               "min_hole_to_hole": 0.25, "min_text_height": 0.7, "min_text_thickness": 0.12, "min_silk_clearance": 0.0}}},
           "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": TRACK,
                                          "via_diameter": 0.6, "via_drill": 0.3}], "meta": {"version": 3}}},
          open(OUT.replace(".kicad_pcb", ".kicad_pro"), "w"), indent=2)
print("saved", OUT, "D1 anode", a, "cathode", k, "R1", r_a, r_b, "JP1", s1, s2)
