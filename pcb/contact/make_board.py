# Generates dev-toh-contact.kicad_pcb: the contact board for the dev cover (cTOH-M indent, see
# ../../model/indent-outline.txt). Run: python3 make_board.py   (KiCad 10 pcbnew module)
#
# Phone coords: u = mm from the phone's right edge, v = mm from its bottom edge, seen from behind.
# KiCad top view = seen from behind the phone (cover side): X = 100 - u, Y = 100 - v.
# B.Cu (bottom, faces the PHONE): 7 contact pads 2.3 mm, flush with the cover's inner surface.
# F.Cu (top, faces the COVER floor): traces + 7 wire pads over the cover's 9 x 3 mm slot (u 25-34, v 9.5-12.5);
# wires are soldered there and leave through the slot. Vias (tented) connect the layers.
# v2: power nets (VIN pin 1, GND pin 2, 5V_OUT pin 7) 0.5 mm wide and 1.2 mm wire pads, for 1 A (e.g. charging the
# phone through pin 1 from a battery cover). VIN and 5V run on B.Cu through the free upper strip; signals stay 0.2 mm on F.Cu.
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I

import os
# Footprint library with Jolla_JP2601_TOH_Contact_7P_P2.90mm_Pads (shared by all cover projects, kept outside this
# repo). Set JOLLATOH_LIB to its path. The generated .kicad_pcb embeds the footprint, so opening it needs no library.
LIB = os.environ.get("JOLLATOH_LIB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kicad", "JollaTOH.pretty"))
OUT = "dev-toh-contact.kicad_pcb"
P = lambda u, v: VECTOR2I(mm(100 - u), mm(100 - v))

PINS = {1: (19.8, 8.45), 2: (19.8, 5.55), 3: (16.9, 8.45), 4: (16.9, 5.55), 5: (14.0, 8.45), 6: (14.0, 5.55), 7: (11.1, 8.45)}
NETS = {1: "VIN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V_OUT"}
LABEL = {1: "VIN", 2: "GND", 3: "ID", 4: "INT", 5: "SCL", 6: "SDA", 7: "5V"}
# board outline = indent minus 0.2 mm
OUTLINE = [(9.1, 3.85), (21.4, 3.85), (21.4, 7.55), (36.2, 7.55), (36.2, 14.3), (9.1, 14.3)]
# routing (F.Cu): via -> lane -> wire pad. Top-row pins go up to lanes above the wire pads,
# bottom-row pins to lanes below; ordered so nothing crosses.
# signal + GND routing (F.Cu): pad -> via (B.Cu stub) -> lane -> wire pad
VIA = {5: (14.0, 10.4), 3: (16.9, 10.4), 6: (12.55, 7.0), 4: (15.45, 7.0), 2: (18.35, 7.0)}
LANE = {5: 13.5, 3: 13.1, 6: 9.2, 4: 8.75, 2: 8.1}
# power on B.Cu: pad -> up to lane -> east -> via next to its wire pad -> short F.Cu stub
BLANE = {7: 13.4, 1: 12.4}
BVIA = {7: (34.1, 11.75), 1: (24.9, 11.75)}
POWER = {1, 2, 7}
WIRE = {7: (32.9, 11.75), 5: (30.6, 11.75), 3: (28.3, 11.75), 1: (26.0, 11.75),
        6: (27.15, 10.25), 4: (29.45, 10.25), 2: (31.75, 10.25)}
TRACK, PTRACK, VIA_D, VIA_DRILL, WIRE_PAD, PWIRE_PAD = 0.2, 0.5, 0.6, 0.3, 1.0, 1.2

b = pcbnew.BOARD()
ds = b.GetDesignSettings()
ds.SetBoardThickness(mm(0.6))
ds.m_MinClearance = mm(0.15); ds.m_TrackMinWidth = mm(0.15); ds.m_ViasMinSize = mm(0.5)
ds.m_MinThroughDrill = mm(0.3); ds.m_CopperEdgeClearance = mm(0.3); ds.m_HoleToHoleMin = mm(0.25)
nets = {}
for n, name in NETS.items():
    ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); nets[n] = ni

for i, (u, v) in enumerate(OUTLINE):
    u2, v2 = OUTLINE[(i + 1) % len(OUTLINE)]
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(P(u, v)); s.SetEnd(P(u2, v2)); s.SetWidth(mm(0.1)); b.Add(s)

fp = pcbnew.FootprintLoad(LIB, "Jolla_JP2601_TOH_Contact_7P_P2.90mm_Pads")
fp.SetReference("J1"); fp.SetPosition(P(*PINS[1]))   # footprint origin = pin 1
fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
for g in list(fp.GraphicalItems()):               # the footprint's F.SilkS outline/pin-1 dot would end up on the
    if g.GetLayer() == pcbnew.F_SilkS: fp.Remove(g)  # cover side, where it's useless and hits the label
b.Add(fp)
for pad in fp.Pads(): pad.SetNet(nets[int(pad.GetNumber())])

wf = pcbnew.FOOTPRINT(b); wf.SetReference("J2"); wf.SetValue("wire pads"); wf.SetPosition(P(29.45, 11.0))
wf.Reference().SetVisible(False); wf.Value().SetVisible(False)
b.Add(wf)
ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
for n, (u, v) in WIRE.items():
    pd = pcbnew.PAD(wf); pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pd.SetShape(pcbnew.PAD_SHAPE_RECT)
    ws = PWIRE_PAD if n in POWER else WIRE_PAD
    pd.SetSize(VECTOR2I(mm(ws), mm(ws))); pd.SetLayerSet(ls); pd.SetNumber(str(n))
    wf.Add(pd); pd.SetPosition(P(u, v)); pd.SetNet(nets[n])

def track(layer, pts, n):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetLayer(layer); t.SetWidth(mm(PTRACK if n in POWER else TRACK)); t.SetNet(nets[n])
        t.SetStart(P(*a)); t.SetEnd(P(*c)); b.Add(t)

def add_via(pos, n):
    via = pcbnew.PCB_VIA(b); via.SetPosition(P(*pos)); via.SetDrill(mm(VIA_DRILL)); via.SetWidth(mm(VIA_D))
    via.SetNet(nets[n]); via.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED); via.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
    b.Add(via)
for n in VIA:                                    # signals + GND
    vu, vv = VIA[n]; add_via(VIA[n], n)
    track(pcbnew.B_Cu, [PINS[n], VIA[n]], n)                                   # contact pad -> via (phone side)
    wu, wv = WIRE[n]
    track(pcbnew.F_Cu, [VIA[n], (vu, LANE[n]), (wu, LANE[n]), (wu, wv)], n)  # via -> wire pad (cover side)
for n in BVIA:                                   # VIN, 5V on the phone side
    (pu, pv), (vu, vv), y = PINS[n], BVIA[n], BLANE[n]
    add_via(BVIA[n], n)
    track(pcbnew.B_Cu, [PINS[n], (pu, y), (vu, y), BVIA[n]], n)
    track(pcbnew.F_Cu, [BVIA[n], WIRE[n]], n)

def text(s, u, v, layer, size=0.7):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer); t.SetPosition(P(u, v))
    t.SetTextSize(VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.12))
    if layer == pcbnew.B_SilkS: t.SetMirrored(True)
    b.Add(t)
for n, (u, v) in WIRE.items():                     # labels next to the wire pads (cover side)
    text(LABEL[n], u, v + (1.25 if v > 11 else -1.25), pcbnew.F_SilkS, 0.8)
text("TOH v2", 22.6, 10.9, pcbnew.F_SilkS, 0.8)

pcbnew.SaveBoard(OUT, b)
# project file with JLCPCB-compatible rules (kicad-cli DRC reads these; without it KiCad's stricter defaults apply)
import json
json.dump({"meta": {"filename": OUT.replace(".kicad_pcb", ".kicad_pro"), "version": 1},
           "board": {"design_settings": {"rules": {
               "min_clearance": 0.15, "min_copper_edge_clearance": 0.3, "min_track_width": 0.15,
               "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3,
               "min_hole_to_hole": 0.25, "min_text_height": 0.8, "min_text_thickness": 0.12, "min_silk_clearance": 0.0}}},
           "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": TRACK,
                                          "via_diameter": VIA_D, "via_drill": VIA_DRILL}], "meta": {"version": 3}}},
          open(OUT.replace(".kicad_pcb", ".kicad_pro"), "w"), indent=2)
print("saved", OUT)
