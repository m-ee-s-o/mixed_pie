from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
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
    font_size = 0
    invoked = False

    def invoke(self, context, event):
        if self.__class__.invoked:
            self.report({'INFO'}, "There's already an existing modal running. Use [Shift + A] if adding new pair.")
            return {'CANCELLED'}
        self.__class__.invoked = True

        DEV_DPI = 72
        if not self.font_size:
            self.__class__.font_size = int(12 * (context.preferences.system.dpi / DEV_DPI))
        self.pairs = set()
        pair = self.get_pair(context)
        if not pair:
            self.report({'INFO'}, "Number of selected vertices should only be 2")
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        self.handler = bpy.types.SpaceImageEditor.draw_handler_add(self.draw_widget, (), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def get_pair(self, context, delete=False):
        pair = set()
        objs = {context.object, *context.selected_objects}
        for obj in objs:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            uvs = set()

            for face in bm.faces:
                for loop_index, loop in enumerate(face.loops):
                    uv_data = loop[uv_layer]
                    uv = tuple(uv_data.uv)
                    if uv_data.select and uv not in uvs:
                        pair.add((data, (face.index, loop_index)))
                        uvs.add(uv)

        pair = tuple(sorted(pair, key=lambda i: i[1]))
        if not delete:
            if len(pair) == 2 and pair not in self.pairs:
                self.pairs.add(pair)
                self.init_indicesToLoops(context)
                self.get_uv_uvVectors()
                return True
        else:
            if pair in self.pairs:
                self.pairs.remove(pair)
                self.init_indicesToLoops(context)
                self.get_uv_uvVectors()

    def init_indicesToLoops(self, context):
        self.objsData_indicesToLoops = {}
        self.objData_loopIndex___uvVector = {}
        objs = {context.object, *context.selected_objects}
        objData_loopIndices = defaultdict(list)

        for pair in self.pairs:
            for objData, indicesToLoop in pair:
                objData_loopIndices[objData].append(indicesToLoop)

        for obj in objs:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            indicesToLoops = IndicesToLoops()

            for face_index, face_loop_index in objData_loopIndices[data]:
                loop = bm.faces[face_index].loops[face_loop_index]
                indicesToLoops.construct(loop)
                self.objData_loopIndex___uvVector[(data, (face_index, face_loop_index))] = tuple(loop[uv_layer].uv)

            if indicesToLoops:
                self.objsData_indicesToLoops[data] = indicesToLoops

    def modal(self, context, event):
        context.area.tag_redraw()

        match event.type:
            case 'RIGHTMOUSE' | 'ESC' if (event.value == 'PRESS'):
                bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
                self.__class__.invoked = False
                return {'CANCELLED'}
            case 'WHEELUPMOUSE' if event.alt:
                self.__class__.font_size += 3
            case 'WHEELDOWNMOUSE' if event.alt:
                self.__class__.font_size -= 3
            case 'A' if event.shift and event.value == 'PRESS':
                pair = self.get_pair(context)
                if not pair:
                    self.report({'INFO'}, "Number of new vertices to add must be two.")
            case 'X' if event.value == 'PRESS':
                self.get_pair(context, delete=True)
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

        img = bpy.context.space_data.image
        img_size = Vector(img.size if img else (256, 256))
        blf.size(0, self.font_size)

        vertices = []
        for pair in self.pairs:
            uv1 = self.uv_uvVectors[self.objData_loopIndex___uvVector[pair[0]]][0]
            uv2 = self.uv_uvVectors[self.objData_loopIndex___uvVector[pair[1]]][0]
            uv_right_angle = Vector((uv1.x, uv2.y))
            # Make triangle, uv1 basis
            adjacent = (uv1, uv_right_angle)
            opposite = (uv_right_angle, uv2)

            for uv in (*adjacent, *opposite):
                vertices.append(vtr(*uv, clip=False))

            for line in (adjacent, opposite):
                p1, p2 = line
                halfway = (p1 + p2) / 2
                halfway = vtr(*halfway, clip=False)
                length = ((p1 - p2) * img_size).magnitude

                blf.position(0, *halfway, 0)
                blf.draw(0, f"{length:.02f}")

        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        lines = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': [(1, 1, 1, 1) for _ in vertices]})
        lines.draw(shader)


def register():
    bpy.utils.register_class(MXD_OT_UV_GetDistance)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_GetDistance)
