# Dev cover: community cTOH-M frame (no-sanding version), laid flat in phone coordinates, plus a wire slot
# through the floor of its existing contact-board indent.
# Phone coords: u = mm from the phone's right edge, v = mm from its bottom edge (seen from behind).
# Output frame = Jolla's toh-3d-model frame: X = -37 + u, Y = -78.8 + v, inside of the cover = +Z,
# outside face at Z = -3.0 (print this face on the bed). cTOH-M plate: inner surface Z = -1.6,
# indent floor Z = -2.2 (0.6 mm deep, pad dimples 0.1 deeper), outside Z = -3.0.
# Run from this folder: freecadcmd -c "exec(open('make_dev_cover.py').read())"
import Part, MeshPart, FreeCAD as App
import os
# Run from this folder (scripts/). Source models: Jolla's toh-designs repo (github.com/sailfishos/toh-designs,
# BSD-3-Clause). Set TOH_DESIGNS to a clone of it; default: the local copy next to this repo.
REPO = os.path.dirname(os.getcwd())
assert os.path.exists(os.path.join(REPO, "ID-modes.md")), "run from the scripts/ folder"
TOH_DESIGNS = os.environ.get("TOH_DESIGNS", os.path.join(REPO, "..", "3d", "og jolla stuff"))
def src(name):
    for sub in ("", "cTOH-M", "jolla"):
        p = os.path.join(TOH_DESIGNS, sub, name)
        if os.path.exists(p): return p
    raise FileNotFoundError(name + " (set TOH_DESIGNS to a clone of github.com/sailfishos/toh-designs)")
OG = src("Optional_Frame-Final1-no sanding.step")
OUT = os.path.join(REPO, "model")
SLOT_U = (25.0, 34.0)   # wire slot, mm from the phone's right edge
SLOT_V = (9.5, 12.5)    # mm from the phone's bottom edge (inside the indent's upper-right arm)
R = 1.0                 # slot corner radius
P = lambda u, v, z: App.Vector(-37.0 + u, -78.8 + v, z)

s = Part.read(OG)
s = s.transformGeometry(App.Matrix(-1, 0, 0, -0.23,  0, 0, -1, -78.65,  0, -1, 0, 0,  0, 0, 0, 1))

# indent outline (for the PCB outline): section just below the plate's inner surface
outline = None
for w in s.slice(App.Vector(0, 0, 1), -1.9):
    b = w.BoundBox
    if 8 < b.XMin + 37 < 10 and b.XMax + 37 > 30 and b.YMax + 78.8 < 20:
        outline = w
raw = [(p.x + 37.0, p.y + 78.8) for p in outline.discretize(Distance=0.05)]
pts = []   # keep corners only (direction change > ~20 deg)
import math
n = len(raw)
for i in range(n):
    a0, a1, a2 = raw[i - 1], raw[i], raw[(i + 1) % n]
    d1 = math.atan2(a1[1] - a0[1], a1[0] - a0[0]); d2 = math.atan2(a2[1] - a1[1], a2[0] - a1[0])
    if abs((d2 - d1 + math.pi) % (2 * math.pi) - math.pi) > 0.35:
        q = (round(a1[0], 2), round(a1[1], 2))
        if not pts or math.dist(q, pts[-1]) > 0.3: pts.append(q)
with open(os.path.join(OUT, "indent-outline.txt"), "w") as f:
    f.write("# cTOH-M contact-board indent outline (u, v) in mm, phone coords (u from right edge, v from bottom edge, seen from behind)\n")
    f.write("# depth 0.6 mm (floor at 0.8 mm plate). PCB outline = this minus ~0.2 mm clearance. Corners, in order.\n")
    for q in pts: f.write("%.2f %.2f\n" % q)
print("indent vertices:", pts)

u0, u1 = SLOT_U; v0, v1 = SLOT_V
face = Part.Face(Part.makePolygon([P(u0, v0, -4), P(u1, v0, -4), P(u1, v1, -4), P(u0, v1, -4), P(u0, v0, -4)]))
tool = face.extrude(App.Vector(0, 0, 3.0))          # Z -4 .. -1: through the floor only, not the rim
tool = tool.makeFillet(R, [e for e in tool.Edges if abs(e.tangentAt(e.FirstParameter).normalize().z) > 0.99])
r = s.cut(tool)
# the cTOH-M STEP is 4 overlapping solids (non-manifold STL); merge them into one
sol = r.Solids
if len(sol) > 1:
    fused = sol[0].fuse(sol[1:]).removeSplitter()
    if fused.isValid() and len(fused.Solids) == 1: r = fused
print("solids in result:", len(r.Solids))
r.exportStep(os.path.join(OUT, "ctohm-dev.step"))
MeshPart.meshFromShape(Shape=r, LinearDeflection=0.02, AngularDeflection=0.15).write(os.path.join(OUT, "ctohm-dev.stl"))
print("volume before", round(s.Volume, 1), "after", round(r.Volume, 1))
