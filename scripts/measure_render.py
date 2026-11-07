# Blender: render the inside of Jolla's cover (toh-3d-model) straight on, as the base image of
# the measuring guide. Orthographic, camera centred on model (CX, CY), PPM pixels per mm.
# Usage: blender -b --python measure_render.py -- <cover.stl> <out.png>
import os, sys, math, bpy
args = sys.argv[sys.argv.index("--") + 1:]
stl, out = args[:2]
# optional: CX CY PPM W_MM H_MM (model coords of the view centre, px/mm, view size in mm)
CX, CY, PPM, W_MM, H_MM = [float(x) for x in args[2:7]] if len(args) >= 7 else (0.0, -0.3, 12.0, 84.0, 166.0)
OUTSIDE = len(args) >= 8 and args[7] == "outside"   # view the outside face (rotated 180 deg about Y)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=os.path.abspath(stl))
if OUTSIDE:
    o = bpy.context.selected_objects[0]; o.rotation_euler = (0, math.pi, 0); bpy.context.view_layer.update()
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.ortho_scale = max(W_MM, H_MM)
co = bpy.data.objects.new("c", cam); bpy.context.scene.collection.objects.link(co)
co.location = (CX, CY, 50); bpy.context.scene.camera = co
sc = bpy.context.scene
try: sc.render.engine = "BLENDER_WORKBENCH"
except TypeError: pass
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.80, 0.80, 0.83)
sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_object_outline = True
sh.background_type = "VIEWPORT"; sh.background_color = (1, 1, 1)
sc.render.film_transparent = False
sc.render.resolution_x = int(W_MM * PPM); sc.render.resolution_y = int(H_MM * PPM)
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
