# cTOH-M camera bump for printing ROOF DOWN (outer face on the bed), without the built-in supports.
# Why: the bump is a cup (roof with the camera holes, ~4 mm walls, a ~1 mm lip at the open edge). Printed open side
# down (make_bump.py), the visible roof is a large bridge over supports. Roof down, the visible face gets the bed's
# surface (matches the frame, which is also printed outside face down), the walls grow straight up, and only the lip
# is a small (< 1 mm) overhang. The source's supports would start in mid-air this way, so they are dropped.
# Run from this folder: freecadcmd -c "exec(open('make_bump_roof_down.py').read())"
import Part, MeshPart, Mesh, FreeCAD as App
import os
REPO = os.path.dirname(os.getcwd())
assert os.path.exists(os.path.join(REPO, "ID-modes.md")), "run from the scripts/ folder"
TOH_DESIGNS = os.environ.get("TOH_DESIGNS", os.path.join(REPO, "..", "3d", "og jolla stuff"))
def src(name):
    for sub in ("", "cTOH-M", "jolla"):
        p = os.path.join(TOH_DESIGNS, sub, name)
        if os.path.exists(p): return p
    raise FileNotFoundError(name + " (set TOH_DESIGNS to a clone of github.com/sailfishos/toh-designs)")
SRC = src("2-Bump-Final2_with_integrated_supports.step")
OUT = os.path.join(REPO, "model", "default-bump", "ctohm-bump-roof-down.stl")
s = Part.read(SRC)
# source: thickness along Y, inner (open) side at Y min, roof at Y max. Rotate +90 deg about X: Y -> -Z, so the roof
# ends up at the bottom
s.transformShape(App.Matrix(1, 0, 0, 0,  0, 0, 1, 0,  0, -1, 0, 0,  0, 0, 0, 1))
body = max(s.Solids, key=lambda x: x.Volume)   # the bump itself; the small solids are the print supports
body.translate(App.Vector(0, 0, -body.BoundBox.ZMin))
b = body.BoundBox
print("solids in source", len(s.Solids), "kept volume %.1f" % body.Volume, "Z %.2f..%.2f" % (b.ZMin, b.ZMax))
MeshPart.meshFromShape(Shape=body, LinearDeflection=0.02, AngularDeflection=0.15).write(OUT)
m = Mesh.Mesh(OUT); print("mesh solid", m.isSolid(), "nonmanifold", m.hasNonManifolds())
