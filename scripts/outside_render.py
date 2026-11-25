# Blender: render the OUTSIDE of the dev cover (model/default-bump/ctohm-dev.stl) with the camera bump (model/default-bump/ctohm-bump.stl)
# put back where it sits on the phone. Two images: straight-on (orthographic) and a close-up of the wire slot.
# Usage (from the repo root): blender -b --python scripts/outside_render.py -- <out_dir>
# Then: python3 scripts/outside_sheet.py <out_dir> renders/wire-pads-outside.png
import os, sys, math, bpy, mathutils
out = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=os.path.abspath("model/default-bump/ctohm-dev.stl")); frame = bpy.context.selected_objects[0]
bpy.ops.wm.stl_import(filepath=os.path.abspath("model/default-bump/ctohm-bump.stl")); bump = bpy.context.selected_objects[0]
# bump STL (print pose, see make_bump.py) -> frame coords (see make_dev_cover.py): X' = -X - 0.23, Y' = Y - 78.65, Z' = -(Z + 1.64)
bump.matrix_world = mathutils.Matrix(((-1, 0, 0, -0.23), (0, 1, 0, -78.65), (0, 0, -1, -1.64), (0, 0, 0, 1)))
# its built-in print supports stand on the inside of the roof: hidden from outside, so they can stay
# turn both 180 deg about Y: outside face (Z = -3) now faces +Z; phone point (u, v) is at X = 37 - u, Y = -78.8 + v
rot = mathutils.Matrix.Rotation(math.pi, 4, "Y")
for o in (frame, bump): o.matrix_world = rot @ o.matrix_world
mat = bpy.data.materials.new("m")
for o in (frame, bump): o.data.materials.append(mat)
sc = bpy.context.scene
try: sc.render.engine = "BLENDER_WORKBENCH"
except TypeError: pass
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.72, 0.74, 0.78)
sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_object_outline = True
sh.show_shadows = True; sh.shadow_intensity = 0.35
sh.background_type = "VIEWPORT"; sh.background_color = (1, 1, 1)
sc.display.shadow_focus = 0.2
sc.render.film_transparent = False; sc.view_settings.view_transform = "Standard"; sc.render.resolution_percentage = 100
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
def render(name, w, h):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = os.path.join(out, name); bpy.ops.render.render(write_still=True)
# 1: straight on, 8 px/mm, 84 x 166 mm view centred on (0, -0.3)
cam.type = "ORTHO"; cam.ortho_scale = 166; co.location = (0, -0.3, 60); co.rotation_euler = (0, 0, 0)
render("straight.png", 84 * 8, 166 * 8)
# 2: close-up of the wire slot, 60 px/mm, 18 x 9 mm view centred on u = 29.5, v = 11 (outside_sheet.py relies on this)
u, v = 29.5, 11.0
cam.ortho_scale = 18; co.location = (37 - u, -78.8 + v, 60)
render("slot.png", 18 * 60, 9 * 60)
