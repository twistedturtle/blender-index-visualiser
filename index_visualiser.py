
bl_info = {
	'name': 'Index Visualiser (BMesh)',
	'author': 'twistedturtle',
	'version': (0, 2, 1),
	'blender': (3, 5, 1),
	'location': 'View3D > Overlays',
	'warning': '',
	'description': 'Display indices of verts, edges and faces in the 3d-view.',
	'wiki_url': '',
	'tracker_url': '',
	'category': '3D View'}


import bpy
import bgl
import blf
import gpu
import bmesh
import mathutils as mu

from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d


font_info = {
	"font_id": 0,
	"handler": None,
}

version = bpy.app.version

def draw_callback_px(context):
	'''Draw the labels'''
	if context.mode != "EDIT_MESH":
		return

	region = context.region
	rv3d = context.space_data.region_3d
	obj = context.active_object
	mw = obj.matrix_world


	font_id = font_info["font_id"]
	text_height = context.scene.indexvis.text_size

	# API: DPI deprecated in 3.4, removed in 4.1 or earlier
	if (version[0] == 3 and version[1] >= 4) or version[0] > 3:
		blf.size(font_id, text_height)
	else:
		blf.size(font_id, text_height, 72)

	me = obj.data
	bm = bmesh.from_edit_mesh(me)


	bgcolor = context.scene.indexvis.bg_color
	fgcolor = context.scene.indexvis.fg_color

	indices = ((0, 1, 2), (2, 1, 3))


	# API: options changed names in 3.4
	if (version[0] == 3 and version[1] >= 4) or version[0] > 3:
		shader = gpu.shader.from_builtin('UNIFORM_COLOR')
	else:
		shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')


	shader.uniform_float("color", bgcolor)

	blf.color(font_id, fgcolor[0], fgcolor[1], fgcolor[2], fgcolor[3])

	selection_modes = bpy.context.tool_settings.mesh_select_mode

	tw, th = blf.dimensions(font_id, "0")

	# Center for edges and faces, offset slightly for verts
	points = []
	if selection_modes[0]:
		yoff = 2.5
		for v in bm.verts:
			if v.select:
				vco = mw @ v.co
				points.append((vco, f"{v.index}"))

	elif selection_modes[1]:
		yoff = -th/2
		for e in bm.edges:
			if e.select:
				vco = e.verts[0].co.lerp(e.verts[1].co, 0.5)
				vco = mw @ vco
				points.append((vco, f"{e.index}"))

	elif selection_modes[2]:
		yoff = -th/2
		for f in bm.faces:
			if f.select:
				n = len(f.verts)
				vco = sum([v.co for v in f.verts], mu.Vector()) / n
				vco = mw @ vco
				points.append((vco, f"{f.index}"))



	# TODO: If labels exist in the same place in the plane
	# 	eg when viewing a cube from the front
	# 	make sure the label the user sees is the one closest to them
	border = 2.5
	b2 = 5
	for vco, index in points:
		x, y = loc3d2d(region, rv3d, vco)
		tw, th = blf.dimensions(font_id, index)

		twh = tw / 2
		vertices = (
			(x-twh,    y+yoff+th+b2),
			(x+twh+b2, y+yoff+th+b2),
			(x-twh,    y+yoff),
			(x+twh+b2, y+yoff)
		)
		batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

		shader.bind()
		batch.draw(shader)

		# Write the index
		blf.position(font_id, x-twh+border, y+yoff+border, 0)
		blf.draw(font_id, index)


class ToggleIndices(bpy.types.Operator):
	"""Toggle display of index labels, for use with keymap"""
	bl_idname = "indexvis.toggleindices"
	bl_label = "Toggle show indices"

	def execute(self, context):
		if context.window_manager.indexvis.show_indices:
			context.window_manager.indexvis.show_indices = False
		else:
			context.window_manager.indexvis.show_indices = True

		return {"FINISHED"}


def toggleDrawHandler(self, context):
	dns = bpy.app.driver_namespace
	if context.window_manager.indexvis.show_indices:
		dns['draw_indices'] = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
	else:
		handler = bpy.app.driver_namespace.get('draw_indices')
		try:
			bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
			del bpy.app.driver_namespace["draw_indices"]
		except:
			pass


def draw_overlay(self, context):
	layout = self.layout
	scene = context.scene
	wm = context.window_manager

	layout.label(text="Index Visualiser")
	layout.prop(wm.indexvis, 'show_indices')
	layout.prop(scene.indexvis, 'text_size')
	layout.prop(scene.indexvis, 'fg_color')
	layout.prop(scene.indexvis, 'bg_color')



class IndexVisSettings(bpy.types.PropertyGroup):
	text_size: bpy.props.IntProperty(name="Font Size", default=12, min=5, max=30)

	bg_color: bpy.props.FloatVectorProperty(
			 name = "Background Colour",
			 subtype = "COLOR",
			 default = (0.0, 0.0, 0.0, 0.6),
			 size = 4
			 )
	fg_color: bpy.props.FloatVectorProperty(
			 name = "Font Colour",
			 subtype = "COLOR",
			 default = (0.0, 1.0, 0.0, 1.0),
			 size = 4
			 )


class IndexVisSettings2(bpy.types.PropertyGroup):
	show_indices:  bpy.props.BoolProperty(name="Indices", default=False, update=toggleDrawHandler)



class Keymaps:
	def __init__(self, name="3D View Generic", space_type="EMPTY", region_type="WINDOW", modal=False, tool=False):
		self.keymaps = []
		self.wm = bpy.context.window_manager
		self.kc = self.wm.keyconfigs.addon
		self.km = km = self.wm.keyconfigs.addon.keymaps.new(name=name, space_type=space_type, region_type=region_type, modal=modal, tool=False)

	def add(self, op, kmi_type, value, kmi_any=False, ctrl=False,  shift=False, alt=False, oskey=False, key_modifier="NONE", direction="ANY", repeat=False, head=False):

		# Add a hotkey
		if self.km:
			idname = op.bl_idname
			kmi = self.km.keymap_items.new(idname, kmi_type, value, any=kmi_any, ctrl=ctrl, shift=shift, alt=alt, oskey=oskey, key_modifier=key_modifier, direction=direction, repeat=repeat, head=head)
			self.keymaps.append(kmi)


	def removeAll(self):
		for kmi in self.keymaps:
			self.km.keymap_items.remove(kmi)
		self.keymaps.clear()



keymaps = Keymaps(space_type="VIEW_3D")



def register():
	bpy.types.VIEW3D_PT_overlay.append(draw_overlay)
	bpy.utils.register_class(IndexVisSettings)
	bpy.utils.register_class(IndexVisSettings2)
	bpy.utils.register_class(ToggleIndices)

	bpy.types.Scene.indexvis = bpy.props.PointerProperty(type=IndexVisSettings)
	bpy.types.WindowManager.indexvis = bpy.props.PointerProperty(type=IndexVisSettings2)

	keymaps.add(ToggleIndices, "F6", "PRESS")




def unregister():
	keymaps.removeAll()

	del bpy.types.WindowManager.indexvis
	del bpy.types.Scene.indexvis


	bpy.utils.unregister_class(ToggleIndices)
	bpy.utils.unregister_class(IndexVisSettings2)
	bpy.utils.unregister_class(IndexVisSettings)
	bpy.types.VIEW3D_PT_overlay.remove(draw_overlay)



if __name__ == "__main__":
	register()