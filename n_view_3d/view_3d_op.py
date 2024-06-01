from math import atan2, ceil, cos, degrees, radians, sin, sqrt
import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, StringProperty
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Euler, Matrix, Quaternion, Vector
# from bpy_extras.view3d_utils import region_2d_to_location_3d


class MXD_OT_ToggleOverlays(Operator):
    bl_idname = "view3d.toggle_overlays"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    mode: StringProperty()

    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'GIZMO':
                return "Toggle gizmos visibility\n\n"    \
                       "Shift: Call gizmos panel"
            case 'OVERLAYS':
                return "Toggle overlays visibility\n\n"  \
                       "Shift: Call overlays panel"

    def invoke(self, context, event):
        match self.mode:
            case 'GIZMO':
                if not event.shift:
                    context.space_data.show_gizmo = not context.space_data.show_gizmo
                else:
                    bpy.ops.wm.call_panel(name="VIEW3D_PT_gizmo_display")
            case 'OVERLAYS':
                if not event.shift:
                    context.space_data.overlay.show_overlays = not context.space_data.overlay.show_overlays
                else:
                    bpy.ops.wm.call_panel(name="VIEW3D_PT_overlay")
        return {'FINISHED'}


class MXD_OT_ToggleStudioLight(Operator):
    bl_idname = "view3d.toggle_studio_light"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = "[MATCAP] basic_1.exr <-> pearl.exr"

    def invoke(self, context, event):
        shading = context.space_data.shading
        if event.shift:
            bpy.ops.wm.context_menu_enum(data_path="space_data.shading.studio_light")
        elif shading.type == 'SOLID' and shading.light == 'MATCAP':
            shading.studio_light = "basic_1.exr" if shading.studio_light != "basic_1.exr" else "pearl.exr"
        else:
            self.report({'INFO'}, "Viewport Shading should be solid matcap.")
            return {'CANCELLED'}
        return {'FINISHED'}


class MXD_OT_MODAL_RotateView(Operator):
    bl_idname = "view3d.rotate_view"
    bl_label = "Rotate View"

    kwargs = {"size":4, "min":0, "max":1, "subtype":'COLOR'}
    arc: FloatVectorProperty(name="Arc", default=(0, 1, 0, 1), **kwargs)
    inner_rad: FloatVectorProperty(name="Inner Radius", default=(0, 1, 0, 0.1), **kwargs)
    outer_rad: FloatVectorProperty(name="Outer Radius", default=(0, 1, 0, 0.5), **kwargs)
    poi_ori: FloatVectorProperty(name="Point: Center", default=(1, 1, 1, 1), **kwargs)
    poi_arc: FloatVectorProperty(name="Point: Arc", default=(0, 1, 0, 1), **kwargs)

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'VIEW_3D')

    def get_coord(self, angle, magnitude):
        angle += self.init_angle
        return ((magnitude * cos(angle)) + self.region_center[0],
                (magnitude * sin(angle)) + self.region_center[1])

    def invoke(self, context, event):
        self.rotation_text = ""
        self.types = bpy.types.Event.bl_rna.properties['type'].enum_items
        self.numbers = [i.identifier for i in self.types
                        if (len(i.name) == 1 or i.identifier.startswith('NUMPAD_')) and i.name[-1].isdigit()]

        region = context.region
        self.region_center = Vector((region.width // 2, region.height // 2))
        cursor_loc = Vector((event.mouse_region_x, event.mouse_region_y))

        # context.region_data.view_location = region_2d_to_location_3d(region, context.region_data, cursor_loc, (0, 0, 0))

        # print(event.mouse_region_x)
        # context.window.cursor_warp(self.region_center[0] + region.x + (region.width // 4), self.region_center[1] + region.y)
        # print(event.mouse_region_x)
        # ?: event.mouse_(location) doesn't seem to update here
        # cursor_loc = (self.region_center[0] + (region.width // 4), self.region_center[1])  # Weird since cursor teleports

        # # self.region_center = cursor_loc  # Since init_angle would be 0, it snaps abruptly

        self.init_region_rot = tuple(context.region_data.view_rotation)
        self.origin = cursor_loc - self.region_center
        self.cur_cursor_loc = self.origin
        self.vertices = [self.region_center, cursor_loc]
        self.init_angle = atan2(self.vertices[1][1] - self.region_center[1], self.vertices[1][0] - self.region_center[0])
        self.rotation = Euler((0, 0, 0))

        context.window.cursor_modal_set('NONE')
        context.window_manager.modal_handler_add(self)
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_line, (), 'WINDOW', 'POST_PIXEL')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        rotation = (f"{degrees(self.rotation[0] * (-1 if self.rotation[0] else 1)):.02f}"
                    if not self.rotation_text else self.rotation_text)
        context.area.header_text_set(f"Rotation: {rotation}°")

        # TODO: Rewrite text inputing
        if event.type in {*self.numbers, 'BACK_SPACE', 'MINUS', 'NUMPAD_MINUS'} and (event.value == 'PRESS'):
            match event.type:
                case 'BACK_SPACE':
                    self.rotation_text = self.rotation_text[:-1]
                case 'MINUS' | 'NUMPAD_MINUS':
                    if len(self.rotation_text):
                        if self.rotation_text[0] != "-":
                            self.rotation_text = f"-{self.rotation_text}"
                        else:
                            self.rotation_text = self.rotation_text.replace("-", "", 1)
                case _:
                    event_type = self.types[event.type].name if not event.type.startswith('NUMPAD_') else event.type[-1]
                    self.rotation_text += event_type

            if self.rotation_text:
                context.window.cursor_modal_restore()
                context.region_data.view_rotation = Quaternion(self.init_region_rot)
                bpy.ops.view3d.view_roll(angle=radians(int(self.rotation_text)))
            else:
                context.window.cursor_modal_set('NONE')
                self.rotate(event)

        elif event.type == 'MOUSEMOVE' and not self.rotation_text:
            self.rotate(event)

        elif event.type in {'LEFTMOUSE', 'RET'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            context.area.header_text_set(None)
            context.window.cursor_modal_restore()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            context.area.header_text_set(None)
            context.region_data.view_rotation = Quaternion(self.init_region_rot)
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        if event.ctrl and not self.rotation_text:
            sign = 1 if (self.rotation[0] > 0) else -1
            value = abs(degrees(self.rotation[0])) % 10
            if round(value, 3) not in {0, 5}:
                n_increment = radians((10 - value if (value > 5) else 5 - value) * sign)
                self.rotation.rotate(Euler((n_increment, 0, 0)))
                bpy.ops.view3d.view_roll(angle=n_increment * -1)

        return {'RUNNING_MODAL'}

    def rotate(self, event):
        self.cur_cursor_loc = Vector((event.mouse_region_x, event.mouse_region_y)) - self.region_center
        angle = (atan2(self.cur_cursor_loc.y, self.cur_cursor_loc.x) - atan2(self.origin.y, self.origin.x))
        increment = angle - (self.rotation[0] % radians(360))
        self.rotation.rotate(Euler((increment, 0, 0)))
        bpy.ops.view3d.view_roll(angle=increment * -1)

    def draw_line(self):
        signed_cur_angle = degrees(self.rotation[0]) if not self.rotation_text else int(self.rotation_text) * -1
        unsigned_cur_angle = abs(signed_cur_angle)
        angle = unsigned_cur_angle if (unsigned_cur_angle < 360) else 360
        sign = 1 if (signed_cur_angle >= 0) else -1

        magnitude = self.cur_cursor_loc.magnitude
        initial_point = self.vertices[1] = self.get_coord(0, magnitude)
        cur_coord = self.get_coord(radians((unsigned_cur_angle % 360) * sign), magnitude)

        mat_rotation = Matrix.Rotation(radians(1 * sign), 2)
        coords = []
        # Every 1 degree angle between 0 and current angle, excluding 0 and current angle
        for _ in range(1, ceil(angle)):
            xy = coords[-1] if coords else (i - self.region_center[index] for index, i in enumerate(initial_point))
            coords.append(list(mat_rotation @ Vector(xy)))

        # coords = (self.get_coord(radians(degree * sign), magnitude) for degree in range(1, ceil(angle)))

        region_coords = []
        for coord in coords:
            for i in range(2):
                coord[i] += self.region_center[i]
            for _ in range(2):
                region_coords.append(coord)

        vertices = self.vertices.copy()
        colors = [self.inner_rad, self.outer_rad]
        if angle:
            vertices += [self.vertices[1], *region_coords,
                         cur_coord if (angle != 360) else self.vertices[1],  # Link last to cur_coord else to init_coord
                         cur_coord, self.region_center]
            colors += [*(self.arc for _ in range(len(region_coords) + 2)), self.outer_rad, self.inner_rad]

        outline_colors = []
        for color in colors:
            color = list(color)
            for channel in range(3):  # Make all channels 0 except alpha
                color[channel] = 0
            outline_colors.append(color)

        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        outline_lines = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': outline_colors})
        outline_points = batch_for_shader(shader, 'POINTS', {
            'pos': (vertices[0], cur_coord),
            'color': ((0, 0, 0, self.poi_ori[-1]), (0, 0, 0, self.poi_arc[-1]))
        })
        # outline = gpu.shader.from_builtin('UNIFORM_COLOR')
        # outline.uniform_float('color', (0, 0, 0, 1))
        # outline_lines = batch_for_shader(outline, 'LINES', {'pos': vertices})
        # outline_points = batch_for_shader(outline, 'POINTS', {'pos': (vertices[0], cur_coord)})
        lines = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': colors})
        points = batch_for_shader(shader, 'POINTS', {'pos': (self.region_center, cur_coord),
                                                     'color': (self.poi_ori, self.poi_arc)})
        state = gpu.state
        state.blend_set('ALPHA')
        state.line_width_set(3)
        state.point_size_set(17)
        outline_lines.draw(shader)
        outline_points.draw(shader)

        # outline_lines.draw(outline)
        # outline_points.draw(outline)
        state.line_width_set(2)
        state.point_size_set(15)
        lines.draw(shader)
        points.draw(shader)
        state.line_width_set(1)
        state.point_size_set(1)
        state.blend_set('NONE')


classes = (
    MXD_OT_ToggleOverlays,
    MXD_OT_ToggleStudioLight,
    MXD_OT_MODAL_RotateView,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
