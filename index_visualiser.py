
bl_info = {
	'name': 'Index Visualiser (BMesh)',
	'author': 'twistedturtle',
	'version': (0, 0, 1),
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


def draw_callback_px(self, context):
	'''Draw the labels'''
	if context.mode != "EDIT_MESH":
		return

	region = context.region
	rv3d = context.space_data.region_3d
	obj = context.active_object
	mw = obj.matrix_world

	text_height = context.scene.indexvis.text_size
	blf.size(0, text_height, 72)
	me = obj.data
	bm = bmesh.from_edit_mesh(me)

	font_id = 0  # handle other fonts?
	bgcolor = context.scene.indexvis.bg_color
	fgcolor = context.scene.indexvis.fg_color

	indices = ((0, 1, 2), (2, 1, 3))
	shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
	shader.uniform_float("color", bgcolor)

	blf.color(font_id, fgcolor[0], fgcolor[1], fgcolor[2], fgcolor[3])

	selection_modes = bpy.context.tool_settings.mesh_select_mode

	points = []
	if selection_modes[0]:
		for v in bm.verts:
			if v.select:
				vco = mw @ v.co
				points.append((vco, f"{v.index}"))

	elif selection_modes[1]:
		for e in bm.edges:
			if e.select:
				vco = e.verts[0].co.lerp(e.verts[1].co, 0.5)
				vco = mw @ vco
				points.append((vco, f"{e.index}"))

	elif selection_modes[2]:
		for f in bm.faces:
			if f.select:
				n = len(f.verts)
				vco = sum([v.co for v in f.verts], mu.Vector()) / n
				vco = mw @ vco
				points.append((vco, f"{f.index}"))

	xoff = 5
	yoff = 2.5
	border = 2.5
	b2 = 5
	for vco, index in points:
		x, y = loc3d2d(region, rv3d, vco)
		tw, th = blf.dimensions(0, index)

		vertices = (
			(x+xoff, y+yoff+th+b2),
			(x+xoff+tw+b2, y+yoff+th+b2),
			(x+xoff, y+yoff),
			(x+xoff+tw+b2, y+yoff)
		)

		batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

		shader.bind()
		batch.draw(shader)

		# Write the index
		blf.position(font_id, x+xoff+border, y+yoff+border, 0)
		blf.draw(font_id, index)


class ModalDrawOperator(bpy.types.Operator):
	"""Draw index labels"""
	bl_idname = "view3d.drawindexlabels"
	bl_label = "Show Indices"

	_handle = None

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def modal(self, context, event):
		if context.area:
			context.area.tag_redraw()

		if not context.scene.indexvis.show_indices:
			bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

			return {"CANCELLED"}

		return {"PASS_THROUGH"}

	def invoke(self, context, event):
		try:
			if context.scene.indexvis.show_indices:
				self._handle = bpy.types.SpaceView3D.draw_handler_add(
					draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')

				context.window_manager.modal_handler_add(self)

				return {"RUNNING_MODAL"}
			else:
				bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

				return {'RUNNING_MODAL'}
		except:
			return {"CANCELLED"}




class ToggleIndices(bpy.types.Operator):
	"""Toggle display of idex labels, for use with keymap"""
	bl_idname = "indexvis.toggleindices"
	bl_label = "Toggle show indices"

	def execute(self, context):
		print("toggle indices")
		if context.scene.indexvis.show_indices:
			context.scene.indexvis.show_indices = False
		else:
			context.scene.indexvis.show_indices = True

		return {"FINISHED"}



def draw_overlay(self, context):
	layout = self.layout
	scene = context.scene

	layout.label(text="Dev")
	layout.prop(scene.indexvis, 'show_indices')
	layout.prop(scene.indexvis, 'text_size')
	layout.prop(scene.indexvis, 'fg_color')
	layout.prop(scene.indexvis, 'bg_color')
	layout.operator(ReloadScripts.bl_idname, text="Reload Scripts")


class ReloadScripts(bpy.types.Operator):
	"""Reload scripts even when the modal operator is running."""

	bl_idname = "indexvis.reloadscripts"
	bl_label = "Reload Scripts"

	def execute(self, context):
		bpy.context.scene.indexvis.old = context.scene.indexvis.show_indices
		context.scene.indexvis.show_indices = False

		if not bpy.app.timers.is_registered(reloadHandler):
			bpy.app.timers.register(reloadHandler, first_interval=0.2)

		return {"FINISHED"}


def reloadHandler():
	'''Reload scripts after the modal has finished'''
	bpy.ops.script.reload()
	if not bpy.app.timers.is_registered(restart):
			bpy.app.timers.register(restart, first_interval=0.0001)


# Need to do it his way to avoid issues (can't remember what now)
def restart():
	bpy.context.scene.indexvis.show_indices = bpy.context.scene.indexvis.old


def startModal(self, context):
	if context.scene.indexvis.show_indices:
		bpy.ops.view3d.drawindexlabels("INVOKE_DEFAULT")


class IndexVisSettings(bpy.types.PropertyGroup):
	text_size: bpy.props.IntProperty(name="Text Size", default=13, min=8, max=20)

	show_indices:  bpy.props.BoolProperty(name="Indices", default=False, update=startModal)
	old:  bpy.props.BoolProperty(name="old", default=False)

	bg_color: bpy.props.FloatVectorProperty(
             name = "BG Color Picker",
             subtype = "COLOR",
             default = (0.0, 0.0, 0.0, 0.6),
             size = 4
             )
	fg_color: bpy.props.FloatVectorProperty(
             name = "FG Color Picker",
             subtype = "COLOR",
             default = (0.0, 1.0, 0.0, 1.0),
             size = 4
             )


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
	bpy.utils.register_class(ModalDrawOperator)
	bpy.utils.register_class(IndexVisSettings)
	bpy.utils.register_class(ReloadScripts)
	bpy.utils.register_class(ToggleIndices)

	bpy.types.Scene.indexvis = bpy.props.PointerProperty(type=IndexVisSettings)

	keymaps.add(ToggleIndices, "F6", "PRESS")
	keymaps.add(ReloadScripts, "F5", "PRESS")


def unregister():
	keymaps.removeAll()
	del bpy.types.Scene.indexvis

	bpy.utils.unregister_class(ToggleIndices)
	bpy.utils.unregister_class(ReloadScripts)
	bpy.utils.unregister_class(IndexVisSettings)
	bpy.utils.unregister_class(ModalDrawOperator)
	bpy.types.VIEW3D_PT_overlay.remove(draw_overlay)


if __name__ == "__main__":
	register()