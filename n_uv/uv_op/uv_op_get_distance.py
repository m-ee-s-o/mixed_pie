from itertools import combinations
import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, IntProperty
from mathutils import Vector
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from .uv_utils import Base_UVOpsPoll, Modal_Get_UV_UvVectors, IndicesToLoops


class MXD_OT_UV_GetDistance(Base_UVOpsPoll, Modal_Get_UV_UvVectors, Operator):
    bl_idname = "uv.get_distance"
    bl_label = "Get Distance"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Get distance between two uvs"

    distance: FloatVectorProperty(name="", size=2, subtype='XYZ')
    font_size: IntProperty()

    def invoke(self, context, event):
        DEV_DPI = 72
        self.font_size = int(12 * (context.preferences.system.dpi / DEV_DPI))
        LIMIT = 3  # Since huge values would freeze blender; Also it doesn't make sense
        self.init_indicesToLoops(context)
        if not (1 < self.loop_counter <= LIMIT):
            self.report({'INFO'}, f"Number of selected vertices should only be 2-{LIMIT}")
            return {'CANCELLED'}
        self.get_uv_uvVectors()

        context.window_manager.modal_handler_add(self)
        self.handler = bpy.types.SpaceImageEditor.draw_handler_add(self.draw_widget, (), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def init_indicesToLoops(self, context):
        self.objsData_indicesToLoops = {}
        self.loop_counter = 0
        objs = {context.object, *context.selected_objects}
        for obj in objs:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            indicesToLoops = IndicesToLoops()
            uvs = set()

            for vert in bm.verts:
                if not vert.select:
                    continue
                for loop in vert.link_loops:
                    uv_data = loop[uv_layer]
                    if uv_data.select:
                        uvs.add(tuple(uv_data.uv))
                        indicesToLoops.construct(loop)

            if indicesToLoops:
                self.objsData_indicesToLoops[data] = indicesToLoops
                self.loop_counter += len(uvs)

    def modal(self, context, event):
        context.area.tag_redraw()

        match event.type:
            case 'RIGHTMOUSE' | 'ESC' if (event.value == 'PRESS'):
                bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
                return {'CANCELLED'}
            case 'WHEELUPMOUSE' if event.alt:
                self.font_size += 3
            case 'WHEELDOWNMOUSE' if event.alt:
                self.font_size -= 3
            case _:
                return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def draw_widget(self):
        try:
            uv_layer, loop = self.validity_tester
            loop[uv_layer]
        except ReferenceError:
            try:
                self.get_uv_uvVectors()
            except ValueError:  # Because of Object Mode when undo-ed too much
                return

        vtr = bpy.context.region.view2d.view_to_region
        pairs_in_view = list(combinations([uvVectors[0] for uvVectors in self.uv_uvVectors.values()], 2))
        pairs = []
        for pair in pairs_in_view:
            pair_in_region = []
            for uv in pair:
                uv = vtr(uv.x, uv.y, clip=False)
                pair_in_region.append(Vector(uv))

            joint = Vector((pair_in_region[0].x, pair_in_region[1].y))
            for i in range(2):
                pairs.append((pair_in_region[i], joint))

        vertices = [uv for pair in pairs for uv in pair]

        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        lines = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': [(1, 1, 1, 1) for _ in vertices]})
        lines.draw(shader)

        halfways = [(uv1 + uv2) / 2 for uv1, uv2 in pairs]
        distances = self.get_distances(pairs_in_view)
        font_id = 0
        blf.size(font_id, self.font_size)
        for i, distance in enumerate(distances):
            for j in range(2):
                halfway = halfways[i * 2 + j]
                text = f"{distance[1 - j]:.02f}"
                text_size = blf.dimensions(font_id, text)
                blf.position(font_id, halfway.x - (text_size[0] / 2), halfway.y, 0)
                blf.draw(font_id, text)

    def get_distances(self, pairs):
        img = bpy.context.space_data.image
        img_size = Vector(img.size if img else (256, 256))
        distances = []

        for pair in pairs:
            distance = (pair[0] - pair[1]) * img_size
            distances.append([abs(i) for i in distance])

        return distances


def register():
    bpy.utils.register_class(MXD_OT_UV_GetDistance)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_GetDistance)
