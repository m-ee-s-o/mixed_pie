import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from mathutils import Vector
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from .uv_utils import Base_UVOpsPoll


class MXD_OT_UV_GetDistance(Base_UVOpsPoll, Operator):
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
        self.paired_with_origin = set()
        pair = self.get_pair(context)
        if not pair:
            self.report({'INFO'}, "Number of selected vertices should only be 2.")
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        self.handler = bpy.types.SpaceImageEditor.draw_handler_add(self.draw_widget, (), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def get_pair(self, context, delete=False):
        pair = []
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
                        pair.append((obj.name, face.index, loop_index))
                        uvs.add(uv)

            bm.free()

        if len(pair) != 2:
            if len(pair) == 1:
                pair = pair[0]
                if not delete:
                    self.paired_with_origin.add(pair)
                    self.init_indicesToLoops()
                    return True
                elif pair in self.paired_with_origin:
                    self.paired_with_origin.remove(pair)
                    self.init_indicesToLoops()
            return

        def sort(pair):
            for i in range(3):
                if pair[0][i] != pair[1][i]:
                    return tuple(sorted(pair, key=lambda p: p[1]))

        pair = sort(pair)
        if not delete:
            if pair not in self.pairs:
                self.pairs.add(pair)
                self.init_indicesToLoops()
                return True
        else:
            if pair in self.pairs:
                self.pairs.remove(pair)
                self.init_indicesToLoops()

    def init_indicesToLoops(self):
        self.uvVector_pair = []
        self.validity_test_loops = []
        self.uv_paired_with_origin = []

        for pair in self.pairs:
            uvVector_pair = []

            for obj_name, face_index, face_loop_index in pair:
                bm = bmesh.from_edit_mesh(bpy.data.objects[obj_name].data)
                uv_layer = bm.loops.layers.uv.active
                loop = bm.faces[face_index].loops[face_loop_index]
                uvVector_pair.append(loop[uv_layer].uv)
                self.validity_test_loops.append(loop)
                bm.free()

            self.uvVector_pair.append(uvVector_pair)
        
        for obj_name, face_index, face_loop_index in self.paired_with_origin:
            bm = bmesh.from_edit_mesh(bpy.data.objects[obj_name].data)
            uv_layer = bm.loops.layers.uv.active
            loop = bm.faces[face_index].loops[face_loop_index]
            self.uv_paired_with_origin.append(loop[uv_layer].uv)
            self.validity_test_loops.append(loop)
            bm.free()

    def modal(self, context, event):
        context.area.tag_redraw()

        match event.type:
            case 'ESC' if event.value == 'PRESS':
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
        for loop in self.validity_test_loops:
            if not loop.is_valid:
                self.init_indicesToLoops()
                break

        vertices = []
        vtr = bpy.context.region.view2d.view_to_region

        space_data = bpy.context.space_data
        img = space_data.image
        img_size = Vector(img.size if img else (256, 256))
        blf.size(0, self.font_size)

        def draw_lines(uv1, uv2):
            uv_right_angle_point = Vector((uv1.x, uv2.y))
            line1 = (uv1, uv_right_angle_point)
            line2 = (uv_right_angle_point, uv2)

            for uv in (*line1, *line2):
                vertices.append(vtr(*uv, clip=False))

            for line in (line1, line2):
                p1, p2 = line
                halfway = (p1 + p2) / 2
                halfway = vtr(*halfway, clip=False)
                length = ((p1 - p2) * img_size).magnitude

                blf.position(0, *halfway, 0)
                blf.draw(0, f"{length:.02f}")        

        cursor = space_data.cursor_location
        if space_data.uv_editor.show_pixel_coords:
            cursor = Vector((cursor[i] / img_size[i] for i in range(2)))
        for uv1 in self.uv_paired_with_origin:
            draw_lines(uv1, cursor)

        for uv1, uv2 in self.uvVector_pair:
            draw_lines(uv1, uv2)

        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        lines = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': [(1, 1, 1, 1) for _ in vertices]})
        lines.draw(shader)


def register():
    bpy.utils.register_class(MXD_OT_UV_GetDistance)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_GetDistance)
