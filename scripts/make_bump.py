# cTOH-M camera bump with its built-in supports, ready for the bed.
# Print orientation: OPEN (inner) side down, roof (outer face) up: the 8 built-in supports stand under the roof
# (0.2 mm gap to it, so they break off). In the source they start 0.16 mm above the bed level; here they are
# extended down to the bed so the slicer doesn't drop their first layer.
# Run from this folder: freecadcmd -c "exec(open('make_bump.py').read())"
import Part, MeshPart, Mesh, FreeCAD as App
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
SRC = src("2-Bump-Final2_with_integrated_supports.step")
OUT = os.path.join(REPO, "model", "ctohm-bump.stl")
s = Part.read(SRC)
# source: thickness along Y, inner side at Y min (1.64), roof at Y max (6.2). Rotate -90 deg about X: Y -> Z
s.transformShape(App.Matrix(1, 0, 0, 0,  0, 0, -1, 0,  0, 1, 0, 0,  0, 0, 0, 1))
body, sups = s.Solids[0], s.Solids[1:]
bed = body.BoundBox.ZMin
parts = [body]
for sp in sups:
    z0 = sp.BoundBox.ZMin
    # bottom faces of the support (facing down, at its lowest level), pushed down to the bed
    feet = [f for f in sp.Faces if abs(f.BoundBox.ZMax - z0) < 1e-3 and abs(f.BoundBox.ZMin - z0) < 1e-3]
    ext = [f.extrude(App.Vector(0, 0, bed - z0)) for f in feet]
    parts.append(sp.fuse(ext).removeSplitter() if ext else sp)
s = Part.makeCompound(parts)
s.translate(App.Vector(0, 0, -bed))
b = s.BoundBox
print("parts", len(parts), "Z %.2f..%.2f" % (b.ZMin, b.ZMax), "support bottoms", sorted(set(round(p.BoundBox.ZMin, 2) for p in parts[1:])))
MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.15).write(OUT)
m = Mesh.Mesh(OUT); print("mesh solid", m.isSolid(), "nonmanifold", m.hasNonManifolds())
