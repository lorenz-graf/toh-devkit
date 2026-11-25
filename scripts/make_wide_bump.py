# Generic wide-bump cover, wide camera bump and its lid (user, 2026-11-25), into model/wide-bump/ (the stock-bump
# parts are in model/default-bump/). Generic: no project-specific parts (projects add theirs on top, e.g. ../toh-ir).
# - model/wide-bump/ctohm-bump.step|stl: copy of the community cTOH-M camera bump made wider, roof outline
#   u 5.7-68.3 (the same 5.7 mm from both long edges; the stock bump is off-centre and the phone rocks on it), same
#   3.2 mm height, camera windows and cavity, same tapered edge; a cone over the flash. It goes into the cover's cutout
#   from the inside, then the cover goes on the phone (like the stock bump). STL: roof down on the bed, no supports.
#   Its back (phone side) is OPEN: a compartment u 6.9-47.5 x v 117.45-150.15, 2.8 high, in the wide part; the flash
#   tube stays closed (pillar); a 6.5 mm wire passage under its lower edge, in line with the cover's cable channel.
# - model/wide-bump/ctohm-lid.step|stl: closes the compartment, 0.8 thick, snaps into a rebate (beads r 0.3 on its long
#   edges), flush with the bump's inner face (the phone also holds it); 6.5 mm wire notch at the channel. Print flat.
# - model/wide-bump/ctohm-cover.step|stl: cTOH-M frame (no-sanding version) with the wide cutout (same taper as the
#   stock opening, 0.1 mm clearance), the magnet-ring recess filled, a blind pocket under the contact board's wire
#   pads (solder joints, ID resistor) and a cable channel from there straight up to the cutout: 6.5 wide (4 wires of
#   1.5 mm side by side), 1.0 deep (floor 0.4). Print the outside face down.
# Phone coords: u = mm from the phone's right edge, v = mm from its bottom edge (seen from behind). Model frame =
# Jolla's toh-3d-model: X = -37 + u, Y = -78.8 + v, inside of the cover = +Z, outside face Z -3.0, inner surface -1.6.
# Run from this folder: freecadcmd -c "exec(open('make_wide_bump.py').read())"
import os, math, Part, MeshPart, Mesh, FreeCAD as App
REPO = os.path.dirname(os.getcwd())
assert os.path.exists(os.path.join(REPO, "ID-modes.md")), "run from the scripts/ folder"
TOH_DESIGNS = os.environ.get("TOH_DESIGNS", os.path.join(REPO, "..", "3d", "og jolla stuff"))
def src(name):
    for sub in ("", "cTOH-M", "jolla"):
        p = os.path.join(TOH_DESIGNS, sub, name)
        if os.path.exists(p): return p
    raise FileNotFoundError(name + " (set TOH_DESIGNS to a clone of github.com/sailfishos/toh-designs)")
OUT = os.path.join(REPO, "model", "wide-bump"); os.makedirs(os.path.join(OUT, "step"), exist_ok=True)   # STLs; STEPs in step/
CTOHM = App.Matrix(-1, 0, 0, -0.23,  0, 0, -1, -78.65,  0, -1, 0, 0,  0, 0, 0, 1)   # cTOH-M -> model frame
P = lambda u, v, z: App.Vector(-37.0 + u, -78.8 + v, z)

# --- bump shape ---
PHONE_W = 74.0
U_MAX = 68.3                      # stock bump's far edge at the roof
U_MIN = PHONE_W - U_MAX           # 5.7
V0, V1 = 116.25, 151.35           # stock bump's extent along the phone
R = 3.0                           # corner radius of the roof outline
ROOF, FACE, BUMP_IN, INNER = -6.2, -3.0, -1.8, -1.6   # roof, outside face, bump's inner end, plate's inner surface
FL0, SLOPE = 1.15, 0.92           # tapered edge: offset from the roof outline at the outside face, growth per mm inwards
CLEAR = 0.1                       # cutout clearance per side
FLASH_U, FLASH_V, FLASH_R, CONE = 44.6, 134.0, 3.0, math.radians(25)
# --- cover ---
RING_C, RING_R, RING_Z = (37.05, 78.6), (21.85, 28.65), -2.3   # cTOH-M magnet-ring recess (0.7 deep): filled
CHANNEL_U, CHANNEL_D = (25.25, 31.75), 1.0                    # 6.5 wide: 4 wires x 1.5 + 0.5
POCKET_U, POCKET_V, POCKET_Z = (25.0, 34.0), (9.5, 14.5), -2.7  # blind pocket under the wire pads (floor 0.3)
# --- open back: compartment + lid ---
ROOF_T, LID_T, REB, LID_CLEAR = 0.8, 0.8, 0.6, 0.1
CAV = (6.9, 47.5, 117.45, 150.15)
Z_CAV0, Z_LID0 = ROOF + ROOF_T, BUMP_IN - LID_T     # -5.4, -2.6
SNAP_U, SNAP_R, SNAP_Z = (20.0, 35.0), 0.3, BUMP_IN - LID_T / 2
NOTCH_D = 2.0                                       # wire notch depth into the lid (its u range = the channel)

def outline(off, z):
    """Roof outline grown by off (rounded rectangle) as a wire at height z (same topology for any off, for lofts)."""
    u0, u1, v0, v1, r = U_MIN - off, U_MAX + off, V0 - off, V1 + off, R + off
    e = [Part.LineSegment(P(u0 + r, v0, z), P(u1 - r, v0, z)),
         Part.ArcOfCircle(Part.Circle(P(u1 - r, v0 + r, z), App.Vector(0, 0, 1), r), -math.pi / 2, 0),
         Part.LineSegment(P(u1, v0 + r, z), P(u1, v1 - r, z)),
         Part.ArcOfCircle(Part.Circle(P(u1 - r, v1 - r, z), App.Vector(0, 0, 1), r), 0, math.pi / 2),
         Part.LineSegment(P(u1 - r, v1, z), P(u0 + r, v1, z)),
         Part.ArcOfCircle(Part.Circle(P(u0 + r, v1 - r, z), App.Vector(0, 0, 1), r), math.pi / 2, math.pi),
         Part.LineSegment(P(u0, v1 - r, z), P(u0, v0 + r, z)),
         Part.ArcOfCircle(Part.Circle(P(u0 + r, v0 + r, z), App.Vector(0, 0, 1), r), math.pi, 3 * math.pi / 2)]
    return Part.Wire(Part.Shape(e).Edges)
flange_off = lambda z: FL0 + (z - FACE) * SLOPE
prism = lambda off, z0, z1: Part.Face(outline(off, z0)).extrude(App.Vector(0, 0, z1 - z0))
loft = lambda z0, z1, extra=0.0: Part.makeLoft([outline(flange_off(z0) + extra, z0), outline(flange_off(z1) + extra, z1)], True, True)

def box(u0, u1, v0, v1, z0, z1, r=0.0):
    f = Part.Face(Part.makePolygon([P(u0, v0, z0), P(u1, v0, z0), P(u1, v1, z0), P(u0, v1, z0), P(u0, v0, z0)]))
    t = f.extrude(App.Vector(0, 0, z1 - z0))
    return t.makeFillet(r, [e for e in t.Edges if abs(e.tangentAt(e.FirstParameter).normalize().z) > 0.99]) if r else t

def one(shape):
    s = shape.removeSplitter()
    assert s.isValid() and len(s.Solids) == 1, (s.isValid(), len(s.Solids))
    return s

def write(shape, name, bed=False, ld=0.02):   # ld 0.02 leaves gaps along the filled ring's seam on the cover
    shape.exportStep(os.path.join(OUT, "step", name + ".step"))
    p = shape.copy()
    if bed: p.translate(App.Vector(0, 0, -p.BoundBox.ZMin))
    f = os.path.join(OUT, name + ".stl"); MeshPart.meshFromShape(Shape=p, LinearDeflection=ld, AngularDeflection=0.1 if ld < 0.02 else 0.15).write(f)
    m = Mesh.Mesh(f); print(name + ".stl", "solid", m.isSolid(), "nonmanifold", m.hasNonManifolds(), "components", m.countComponents())

# --- bump: wide outer body + the stock bump's own cavity, windows and walls ---
stock = max(Part.read(src("2-Bump-Final2_with_integrated_supports.step")).Solids, key=lambda x: x.Volume).transformGeometry(CTOHM)
body = prism(0, ROOF, FACE)
try:
    body = body.makeFillet(0.3, [e for e in body.Edges if abs(e.BoundBox.ZMax - ROOF) < 1e-6 and abs(e.BoundBox.ZMin - ROOF) < 1e-6])
except Exception as ex:
    print("roof edge fillet skipped:", ex)
body = body.fuse(loft(FACE, BUMP_IN))
def inner_at(z, z0, z1):   # the stock cavity's outline at height z, as a prism z0..z1
    w = min(stock.slice(App.Vector(0, 0, 1), z), key=lambda w: w.BoundBox.DiagonalLength)
    w.translate(App.Vector(0, 0, z0 - z))
    return Part.Face(w).extrude(App.Vector(0, 0, z1 - z0))
body = body.cut(inner_at(-3.05, ROOF - 1, FACE)).cut(inner_at(-1.85, FACE, BUMP_IN + 1))
def flash_cone(r_add=0.0):
    h = BUMP_IN - ROOF + 0.2; r0 = FLASH_R + r_add
    return Part.makeCone(r0, r0 + h * math.tan(CONE), h, P(FLASH_U, FLASH_V, BUMP_IN + 0.1), App.Vector(0, 0, -1))
bump = body.fuse(stock).cut(flash_cone())
# open back: compartment + lid seat, snap grooves, flash pillar, wire passage
u0, u1, v0, v1 = CAV
space = box(u0, u1, v0, v1, Z_CAV0, Z_LID0 + 0.01, r=1.5).fuse(box(u0 - REB, u1 + REB, v0 - REB, v1 + REB, Z_LID0, BUMP_IN + 0.5, r=1.5 + REB))
grooves = [box(SNAP_U[0], SNAP_U[1], v - SNAP_R - 0.05, v + SNAP_R + 0.05, SNAP_Z - SNAP_R - 0.05, SNAP_Z + SNAP_R + 0.05) for v in (v0 - REB, v1 + REB)]
pillar = flash_cone(1.0).common(box(u0 - REB, u1 + REB, v0, v1, Z_CAV0 - 0.1, BUMP_IN, 0))
bump = bump.cut(space.fuse(grooves)).fuse(pillar).cut(flash_cone())
bump = one(bump.cut(box(CHANNEL_U[0], CHANNEL_U[1], V0 - 5.0, v0 - REB + 0.5, Z_LID0, BUMP_IN + 0.5)))
lid = box(u0 - REB + LID_CLEAR, u1 + REB - LID_CLEAR, v0 - REB + LID_CLEAR, v1 + REB - LID_CLEAR, Z_LID0, BUMP_IN, r=1.5 + REB - LID_CLEAR)
lid = lid.cut(Part.makeCylinder(FLASH_R + 1.0 + math.tan(CONE) * LID_T + 0.2, 2, P(FLASH_U, FLASH_V, Z_LID0 - 0.5)))
for v in (v0 - REB + LID_CLEAR, v1 + REB - LID_CLEAR):
    lid = lid.fuse(Part.makeCylinder(SNAP_R, SNAP_U[1] - SNAP_U[0] - 2, P(SNAP_U[0] + 1, v, SNAP_Z), App.Vector(1, 0, 0)))
lid = one(lid.cut(box(CHANNEL_U[0], CHANNEL_U[1], v0 - REB - 1, v0 - REB + LID_CLEAR + NOTCH_D, Z_LID0 - 1, BUMP_IN + 1)))  # after the beads

# --- cover ---
s = Part.read(src("Optional_Frame-Final1-no sanding.step")).transformGeometry(CTOHM)
if len(s.Solids) > 1:   # the cTOH-M STEP is several overlapping solids
    s = s.Solids[0].fuse(s.Solids[1:])
c = P(RING_C[0], RING_C[1], RING_Z - 0.05)
ring = Part.makeCylinder(RING_R[1] + 0.05, INNER - RING_Z + 0.05, c).cut(Part.makeCylinder(RING_R[0] - 0.05, INNER - RING_Z + 0.05, c))
cutout = prism(FL0 + CLEAR, FACE - 1.0, FACE).fuse([loft(FACE, INNER, CLEAR), prism(flange_off(INNER) + CLEAR, INNER, INNER + 0.1)])
cut_v = V0 - flange_off(INNER) - CLEAR          # the cutout's lower edge at the inner surface (~113.7)
cover = s.fuse(ring).cut(cutout)
cover = cover.cut(box(POCKET_U[0], POCKET_U[1], POCKET_V[0], POCKET_V[1], POCKET_Z, INNER + 1.0, r=1.0))
cover = one(cover.cut(box(CHANNEL_U[0], CHANNEL_U[1], POCKET_V[1] - 1, cut_v + 1, INNER - CHANNEL_D, INNER + 1.0, r=0.5)))

print("bump u %.2f-%.2f, roof %.1f above the outside face; channel u %.2f-%.2f v %.1f-%.1f, %.1f deep" %
      (U_MIN, U_MAX, FACE - ROOF, CHANNEL_U[0], CHANNEL_U[1], POCKET_V[1], cut_v, CHANNEL_D))
print("CHECK overlap bump/cover %.3f, lid/cover %.3f, bump/lid %.3f mm3" % (bump.common(cover).Volume, lid.common(cover).Volume, bump.common(lid).Volume))
path = box(CHANNEL_U[0] + 0.3, CHANNEL_U[1] - 0.3, POCKET_V[1], v0 + 1.0, Z_LID0 + 0.1, BUMP_IN - 0.1)   # wire path, 0.6 high
print("CHECK wire path channel -> passage -> lid notch -> compartment blocked by: cover %.3f, bump %.3f, lid %.3f mm3" %
      (path.common(cover).Volume, path.common(bump).Volume, path.common(lid).Volume))
write(bump, "ctohm-bump", bed=True)     # roof (lowest Z) on the bed
write(lid, "ctohm-lid", bed=True)       # flat
write(cover, "ctohm-cover", ld=0.01)    # outside face at Z -3.0, as the other covers
