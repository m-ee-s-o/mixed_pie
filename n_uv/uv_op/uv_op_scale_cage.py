from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import  BoolProperty, BoolVectorProperty 
import bmesh
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from ...a_utils.utils_func import get_center, get_input_keys
from ...f_ui.utils.utils_box import make_box
from ...f_ui.utils_panel import MXD_OT_Utils_Panel
from ...f_ui.utils.utils import Attr_Holder, EventTypeIntercepter
from .uv_utils import Base_UVOpsPoll, Modal_Get_UV_UvVectors, IndicesToLoops, SearchUV


class MXD_OT_UV_ScaleCage(Base_UVOpsPoll, Operator):
    bl_idname = "uv.scale_cage"
    bl_label = "Scale Cage"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    lock_aspect_ratio: BoolProperty(default=True)
    axis: BoolVectorProperty(size=2, default=(True, True))
    separate_selection_groups: BoolProperty(default=True)

    class SelectionGroup(Modal_Get_UV_UvVectors):
        POINTS_BOUND_DEF = (
            ("min_x", "min_y"),        # Bottom Left
            ("center_x", "min_y"),     # Bottom
            ("max_x", "min_y"),        # Bottom Right

            ("max_x", "center_y"),     # Right

            ("max_x", "max_y"),        # Top Right
            ("center_x", "max_y"),     # Top
            ("min_x", "max_y"),        # Top Left

            ("min_x", "center_y"),     # Left
        )
        CROSS = {1: 1, 3: 0, 5: 1, 7: 0}  # BottomRightTopLeft and their respective axis (0: x, 1: y)

        def __init__(self, objsData_indicesToLoops, UI_SCALE):
            self.UI_SCALE = UI_SCALE
            self.objsData_indicesToLoops = objsData_indicesToLoops
            self.objs_data = tuple(objsData_indicesToLoops.keys())
            self.vertices = []      # For drawing widget
            self.active = []        # For when the mouse is over a point
            self.index = None       # Index of which point the mouse is hovering
            self.last_index = None  # When group is in MXD_OT_UV_ScaleCage.other_active (scale with others) and index was changed, this is so that...
                                    # ...hover scaling still works but changing index should be done through click
            self.origin = None
            self.is_center_origin = False  # True when shift-ed

            self.initialize()
            self.shift_points = self.get_points()      # Points used while shift-ing
            self.org_uv_uvVectors = self.uv_uvVectors  # A constant copy which is only used to revert uvs when operation is cancelled
            self.new_uv_uvVectors = {}                 # Modification is always done with prior values when mouse is held; Only updates when released

        def initialize(self):
            self.get_uv_uvVectors()
            uv_uvVectors = self.uv_uvVectors
            x = sorted(uv_uvVectors, key=lambda uv: uv[0])
            y = sorted(uv_uvVectors, key=lambda uv: uv[1])
            self._min_x = uv_uvVectors[x[0]][0]
            self._max_x = uv_uvVectors[x[-1]][0]
            self._min_y = uv_uvVectors[y[0]][0]
            self._max_y = uv_uvVectors[y[-1]][0]
            self.center = self.get_bounds_center()
            if self.is_center_origin:
                self.origin = self.center
            elif self.index is not None:
                self.origin = Vector(self.get_points()[self.index - 4])

        @property
        def min_x(self):
            return self._min_x.x

        @property
        def max_x(self):
            return self._max_x.x

        @property
        def min_y(self):
            return self._min_y.y

        @property
        def max_y(self):
            return self._max_y.y

        @property
        def center_x(self):
            return get_center(self.min_x, self.max_x)

        @property
        def center_y(self):
            return get_center(self.min_y, self.max_y)   

        def get_bounds_center(self):
            return Vector((self.center_x, self.center_y))

        def get_points(self):
            return [(getattr(self, x), getattr(self, y)) for x, y in self.POINTS_BOUND_DEF]

        def get_points_area(self):
            if not self.validity_test_loop.is_valid:
                self.initialize()

            vtr = bpy.context.region.view2d.view_to_region
            vertices = self.vertices
            vertices.clear()
            self.active.clear()

            points_region = [Vector(vtr(x, y, clip=False)) for x, y in self.get_points()]
            self.corners = [points_region[i] for i in (0, 2, 4, 6)]  # BottomLeft, BottomRight, TopRight, TopLeft
            corners = [corner for corner in self.corners for _ in range(2)]
            corners.append(corners.pop(0))
            vertices.extend(corners)

            SIDE = 14 * self.UI_SCALE
            points_area = []
            for index, point in enumerate(points_region):
                box_points, point_corners = make_box(point, SIDE, SIDE, return_corners=True, origin_point='CENTER')
                verts = self.active if (index == self.index) and self.origin else vertices
                verts.extend(box_points)
                points_area.append(point_corners)

            return points_area

        def scale_uv(self, scale_factor, lock_aspect_ratio):
            self.new_uv_uvVectors = {}
            origin = self.origin
            scale_factor = Vector(scale_factor)

            if (axis := self.CROSS.get(self.index)) is not None:
                if not lock_aspect_ratio:
                    o_axis = 1 - axis
                    scale_factor[o_axis] = 1

            for uv, uv_uvVectors in self.uv_uvVectors.items():
                uv = Vector(uv)
                norm_uv = uv - origin
                new_uv = norm_uv * scale_factor + origin
                for uvVector in uv_uvVectors:
                    uvVector[:] = new_uv
                self.new_uv_uvVectors[tuple(new_uv)] = uv_uvVectors
            self.update_data()

        def move_uv(self, offset):
            # TODO: Remove move, redundant
            self.new_uv_uvVectors = defaultdict(list)
            offset = Vector(offset)
            for uv, uvVectors in self.uv_uvVectors.items():
                new_uv = Vector(uv) + offset
                for uvVector in uvVectors:
                    uvVector[:] = new_uv
                self.new_uv_uvVectors[tuple(new_uv)] = uvVectors

            self.update_data()

        def replace_values(self):
            self.uv_uvVectors = self.new_uv_uvVectors
            self.shift_points = self.get_points()
            self.center = self.get_bounds_center()

        def revert_uvVectors(self, to_org=False, to_this=None):
            self.new_uv_uvVectors = {}
            this = to_this if to_this else self.org_uv_uvVectors if to_org else self.uv_uvVectors
            if isinstance(this, dict):
                this = tuple(this.keys())
            for uv, uvVectors in zip(this, self.uv_uvVectors.values()):
                for uvVector in uvVectors:
                    uvVector[:] = uv
                self.new_uv_uvVectors[uv] = uvVectors
            self.replace_values()
            self.update_data()

        def update_data(self):
            for data in self.objs_data:
                bmesh.update_edit_mesh(data)

    class Action_uvVectors:
        def __init__(self, undo_groups_uv_uvVectors: dict):
            self.undo_groups_uv_uvVectors = undo_groups_uv_uvVectors
            self.redo_groups_uv_uvVectors = None

        def undo(self):
            for group, uv_uvVectors in self.undo_groups_uv_uvVectors.items():
                group.revert_uvVectors(to_this=uv_uvVectors)        

        def redo(self):
            for group, uv_uvVectors in self.redo_groups_uv_uvVectors.items():
                group.revert_uvVectors(to_this=uv_uvVectors)        

    class Action_SelectionGroups:
        def __init__(self, op):
            self.op = op
            self.last_separate_selection_groups = self.current_separate_selection_groups = op.separate_selection_groups
            self.last_selection_groups = op.selection_groups.copy()

        @property
        def current_selection_groups(self):
            return self._current_selection_groups
        
        @current_selection_groups.setter
        def current_selection_groups(self, value: list):
            self._current_selection_groups = value.copy()

        def undo(self):
            self.op.selection_groups = self.last_selection_groups
            self.op.separate_selection_groups = self.last_separate_selection_groups

        def redo(self):
            self.op.selection_groups = self.current_selection_groups
            self.op.separate_selection_groups = self.current_separate_selection_groups

    class UndoStack(list):
        def __init__(self, __iterable=None):
            super().__init__(__iterable if __iterable else list())
            self.current_action_index = -1

        def append(self, __object):
            self.current_action_index += 1
            self[:] = self[:self.current_action_index]  # Cut redos
            super().append(__object)

        def undo(self, op):
            current_action_index = self.current_action_index
            if current_action_index < 0:
                return
            action = self[current_action_index]
            match action.__class__:
                case op.Action_SelectionGroups:
                    action.undo()
                case op.Action_uvVectors:
                    action.undo()
            self.current_action_index -= 1

        def redo(self, op):
            if self.current_action_index == len(self) - 1:
                return
            self.current_action_index += 1
            action = self[self.current_action_index]
            match action.__class__:
                case op.Action_uvVectors:
                    action.redo()
                case op.Action_SelectionGroups:
                    action.redo()

    @property
    def custom_value(self):
        return getattr(self, "_custom_value", None)

    @custom_value.setter
    def custom_value(self, value):
        self._custom_value = value
        if not value:
            match self.in_area:
                case 'POINT':
                    self.scale_factor = [1, 1]
                    self.scale_selection_groups(self.scale_factor)
                case 'CAGE':
                    self.offset = [0, 0]
                    self.active_group.move_uv(self.offset)
            return

        err = None
        try:
            answer = eval(value)
            if answer == ...:
                raise SyntaxError
            match self.in_area:
                case 'POINT':
                    factor = self.scale_factor = getattr(self, "scale_factor", [1, 1])
                    for i, axis in enumerate(self.axis):
                        factor[i] = answer if axis else 1
                    self.scale_selection_groups(factor)
                case 'CAGE':
                    offset = self.offset = getattr(self, "offset", [0, 0])
                    for i, axis in enumerate(self.axis):
                        offset[i] = answer if axis else 0
                    self.active_group.move_uv(offset)
        except (ZeroDivisionError, SyntaxError) as e:
            err = e.__class__.__name__

        self.err_custom_value = err

    def invoke(self, context, event):
        self.undo_stack = self.UndoStack()
        self.input_keys = get_input_keys()

        DEV_DPI = 72
        self.ui_scale = (context.preferences.system.dpi / DEV_DPI)
        self.POINT_SIZE = 7 * self.ui_scale

        self.is_widget_shown = True
        self.toggle_free_mode = False

        self.in_area = False
        self.init_cur_loc = None

        self.selection_groups = []
        self.active_group = None

        self.scale_factor = [1, 1]
        self.offset = [0, 0]

        if not self.get_selection_groups(context, undo=False):
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        self.handler = bpy.types.SpaceImageEditor.draw_handler_add(self.draw_widget, (), 'WINDOW', 'POST_PIXEL')
        self.attr_holder = Attr_Holder()
        return {'RUNNING_MODAL'}

    def get_selection_groups(self, context, append=False, undo=True, action=None):
        objs = {context.object, *context.selected_objects}
        selection_groups = self.selection_groups
        past_len = len(selection_groups)
        if undo:
            action = self.Action_SelectionGroups(self)

        if not append:
            selection_groups.clear()
            self.other_active = set()
            self.active_loops = set()

        if self.separate_selection_groups and not append:
            for obj in objs:
                data = obj.data
                bm = bmesh.from_edit_mesh(data)
                uv_layer = bm.loops.layers.uv.active

                loops_done = set()
                for vert in bm.verts:
                    if not vert.select:
                        continue
                    for loop in vert.link_loops:
                        if loop in loops_done:
                            continue
                        uv_data = loop[uv_layer]
                        if not uv_data.select:
                            continue
                        loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, tuple(uv_data.uv), active_only=True)
                        loops_done.update(loops)
                        self.active_loops.update(loops)
                        selection_groups.append(self.SelectionGroup({data: indicesToLoops}, self.ui_scale))            
                bm.free()
        else:
            objsData_indicesToLoops = {}
            for obj in objs:
                data = obj.data
                bm = bmesh.from_edit_mesh(data)
                uv_layer = bm.loops.layers.uv.active
                indicesToLoops = IndicesToLoops()

                for face in bm.faces:
                    if not face.select:
                        continue
                    for loop in face.loops:
                        if loop in self.active_loops:
                            continue
                        uv_data = loop[uv_layer]
                        if uv_data.select:
                            indicesToLoops.construct(loop)
                            self.active_loops.add(loop)
                bm.free()

                if indicesToLoops:
                    objsData_indicesToLoops[data] = indicesToLoops

            if objsData_indicesToLoops:
                group = self.SelectionGroup(objsData_indicesToLoops, self.ui_scale)
                selection_groups.append(group)

        if past_len == len(selection_groups):
            return
        if action:
            action.current_selection_groups = selection_groups
            self.undo_stack.append(action)
        return selection_groups

    def modal(self, context, event):
        event = EventTypeIntercepter(event, self.ui_scale, self.attr_holder)
        window = context.window
        area = context.area
        area.tag_redraw()
        press = (event.value == 'PRESS')

        if getattr(self, "finished", False):
            bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
            window.cursor_modal_restore()
            area.header_text_set(None)
            return {'FINISHED'}

        if getattr(self, "error", None):
            bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
            window.cursor_modal_restore()
            area.header_text_set(None)
            return {'CANCELLED'}

        if event.type == 'RIGHTMOUSE' and press:
            self.panel_shown = True
            self.moved = False
            self.panel_origin = event.cursor
            event.handled = True
            window.cursor_modal_restore()

        if getattr(self, "panel_shown", False):
            ret = MXD_OT_Utils_Panel.panel_listener(self, context, event)
            if ret == {'CANCELLED'}:
                self.panel_shown = False
            return {'RUNNING_MODAL'}

        if event.handled:
            return {'RUNNING_MODAL'}

        if (event.type == 'Q') and press and event.shift:
            self.toggle_free_mode = not self.toggle_free_mode

            if self.toggle_free_mode:
                window.cursor_modal_restore()
            else:
                for group in self.selection_groups:
                    group.initialize()
                    dataChanged = False
                    for uv_data in group.uv_data:
                        if uv_data.select:
                            continue
                        uv_data.select = True
                        uv_data.select_edge = True
                        dataChanged = True
                    if dataChanged:
                        group.update_data()

        if self.toggle_free_mode:
            area.header_text_set("Free Key Mode")
            return {'PASS_THROUGH'}

        in_area = self.in_area
        self.cursor = event.cursor
        init_cur_loc = self.init_cur_loc

        self.set_header_text(area)

        keys = self.input_keys
        custom_value = self.custom_value

        active_group = self.active_group
        other_active = self.other_active

        if in_area and press:
            match event.type:
                case 'EIGHT' if event.shift:
                    if custom_value is None:
                        self.init_cur_loc = True
                        window.cursor_modal_restore()
                        self.custom_value = "*"
                    else:
                        self.custom_value += "*"

                case _ as e if e in keys:
                    val = keys[e]
                    if custom_value is None:
                        self.init_cur_loc = True
                        window.cursor_modal_restore()
                        self.custom_value = val
                    else:
                        self.custom_value += val

                case 'BACK_SPACE' | 'DEL':
                    if custom_value:
                        self.custom_value = custom_value[:-1]

                case 'LEFTMOUSE' | 'RET' if custom_value and not event.ctrl:
                    self.confirm(context, event)
                    self.custom_value = None
                    self.err_custom_value = None

                case 'RIGHTMOUSE' | 'ESC' if init_cur_loc:
                    self.cancel_current_action(context)
                    self.custom_value = None
                    self.err_custom_value = None
                    return {'RUNNING_MODAL'}

                case 'X':
                    if (ret := self.toggle_contraint_axis(1, (True, False))):
                        return ret

                case 'Y':
                    if (ret := self.toggle_contraint_axis(0, (False, True))):
                        return ret

                case _ as e if custom_value is not None and ('MOUSE' in e):
                    return {'PASS_THROUGH'}

        if custom_value is not None:
            if active_group and event.type.endswith('SHIFT') and (in_area == 'POINT') and (event.value == 'RELEASE'):
                active_group.is_center_origin = False
            return {'RUNNING_MODAL'}

        match event.type:
            case 'MOUSEMOVE':
                self.check_cursor_location(context)

            case 'DRAGMOVE' if init_cur_loc:
                match in_area:
                    case 'POINT':
                        self.scale_selection_groups()
                    case 'CAGE':
                        active_group.move_uv(self.get_offset())

            case 'LEFTMOUSE':
                if event.alt:
                    self.finished = True
                    return {'RUNNING_MODAL'}
                if press:
                    self.attr_holder.parse_dragmove_immediately_regardless_of_distance = True
                    if in_area and not event.ctrl:
                        self.init_cur_loc = event.cursor
                else:
                    self.attr_holder.parse_dragmove_immediately_regardless_of_distance = False
                    self.confirm(context, event)

            case 'RET':
                bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
                area.header_text_set(None)
                return {'FINISHED'}

            case 'ESC' if press:
                bpy.types.SpaceImageEditor.draw_handler_remove(self.handler, 'WINDOW')
                area.header_text_set(None)
                window.cursor_modal_restore()

                self.revert_uvVectors(to_org=True)
                return {'CANCELLED'}

            case 'RIGHTMOUSE' if press:
                return {'RUNNING_MODAL'}

            case _ as e if e.endswith('SHIFT') and active_group and (in_area == 'POINT'):
                if active_group not in other_active:
                    origin = active_group.origin
                    if origin:
                        if press:
                            origin[:] = active_group.center
                            active_group.is_center_origin = True
                        else:
                            origin[:] = Vector(active_group.shift_points[active_group.index - 4])
                    if (event.value == 'RELEASE'):
                        active_group.is_center_origin = False
                if init_cur_loc:
                    self.scale_selection_groups()

            case 'A' if press and (in_area != 'CAGE'):
                self.lock_aspect_ratio = not self.lock_aspect_ratio
                if init_cur_loc:
                    self.scale_selection_groups()

            case 'Z' if press:
                undo_stack = self.undo_stack
                if press:
                    if event.ctrl and not event.shift:
                        undo_stack.undo(self)
                    elif event.ctrl and event.shift:
                        undo_stack.redo(self)

            case _ as e if 'MOUSE' in e:
                return {'PASS_THROUGH'}

            # case _ if press: 
            #     return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}
    
    def draw_structure(self, context, event, layout):
        def finish():
            self.finished = True
            self.panel_shown = False
        def toggle_widget():
            self.is_widget_shown = not self.is_widget_shown
        def separate_selection_groups():
            action = self.Action_SelectionGroups(self)  # Also gets last self.separate_selection_groups
            action.current_separate_selection_groups = not action.last_separate_selection_groups
            self.separate_selection_groups = not self.separate_selection_groups
            self.get_selection_groups(context, undo=False, action=action)
            self.check_cursor_location(context)
        def unincluded_active_vertices():
            self.get_selection_groups(context, append=True)
            self.report({'INFO'}, "Done!")

        def make_center_the_origin_for_all():
            for group in self.selection_groups:
                self.other_active.add(group)
                group.index = None
                group.last_index = None
                group.is_center_origin = True
                group.origin = group.center
        def remove_all_origin():
            for group in self.selection_groups:
                if group not in self.other_active:
                    continue
                self.other_active.remove(group)
                group.index = None
                group.last_index = None
                group.is_center_origin = False
                group.origin = None

        width = 500 * layout.ui_scale
        layout.custom_spacing_between_children = 1
        layout.button(f"{'Unite' if self.separate_selection_groups else 'Separate'} Selection Groups", separate_selection_groups, emboss=False).width = width
        layout.button("Include Unincluded Active Vertices", unincluded_active_vertices, emboss=False).width = width
        layout.button("All Center As Origin", make_center_the_origin_for_all, emboss=False).width = width
        layout.button("Remove All Origin", remove_all_origin, emboss=False).width = width
        layout.button(f"{'Hide' if self.is_widget_shown else 'Show'} Widget", toggle_widget, emboss=False).width = width
        layout.button("Finish Operation", finish, emboss=False, shortcut="Alt + LeftClick").width = width

    def set_header_text(self, area):
        text = []
        lock_aspect_ratio = self.lock_aspect_ratio
        axis = self.axis
        set_axis_text = self.set_axis_text
        in_area = self.in_area
        active_group = self.active_group

        match in_area:
            case 'POINT':
                colon = True
                scale = self.scale_factor
                if active_group and (index := active_group.CROSS.get(active_group.index)) is not None:
                    factor = set_axis_text(index, scale, axis_label=(not lock_aspect_ratio))
                else:
                    if lock_aspect_ratio:
                        factor = set_axis_text(0, scale, axis_label=False)
                    else:
                        tmp = []
                        if axis[0]:
                            set_axis_text(0, scale, tmp)
                        if axis[1]:
                            set_axis_text(1, scale, tmp)
                        factor = "    ".join(tmp)
                        colon = False
                text.append(f"Scale{':' if colon else '   '} {factor}")
            case 'CAGE':
                offset = self.offset
                if axis[0]:
                    set_axis_text(0, offset, text)
                if axis[1]:
                    set_axis_text(1, offset, text)

        if in_area != 'CAGE':  # None or 'POINT'
            text.append(f"(A) Lock Aspect Ratio: {lock_aspect_ratio}")
        # TODO: Put a Key Map
        if in_area:
            text.append("(X) (Y) Constraint Axis")
        if in_area == 'POINT':
            text.append("(Shift) Center as Origin")
            text.append("(Ctrl + LeftClick) Preserve Point State")

        area.header_text_set("            ".join(text))

    def set_axis_text(self, index, answer_list, append_to=None, axis_label=True):
        has_append_to = (append_to is not None)
        txt = ("X: " if (index == 0) else "Y: ") if axis_label else ""
        if (val := self.custom_value) is not None:
            txt += f"[{val}] = "
        txt += err if (err := getattr(self, "err_custom_value", None)) else f"{answer_list[index]:.4f}"
        if not has_append_to:
            return txt
        append_to.append(txt)

    def toggle_contraint_axis(self, other_axis_index, value):
        is_point = (self.in_area == 'POINT')
        custom_value_exist = (self.custom_value is not None)
        axis = self.axis
        if is_point and self.lock_aspect_ratio:
            axis[:] = (True, True)
            return {'RUNNING_MODAL'}

        axis[:] = (True, True) if not axis[other_axis_index] else value  # Toggle
        self.custom_value = self.custom_value  # Refresh scale_factor and offset

        if is_point:
            if sum(axis) == 1:
                self.scale_factor[other_axis_index] = 1
            arg = [self.scale_factor] if custom_value_exist or not self.init_cur_loc else []
            self.scale_selection_groups(*arg)
        else:
            if sum(axis) == 1:
                self.offset[other_axis_index] = 0
            arg = [self.offset] if custom_value_exist or not self.init_cur_loc else [self.get_offset()]
            self.active_group.move_uv(*arg)

    def check_cursor_location(self, context):
        window = context.window
        cursor = self.cursor
        other_active = self.other_active
        selection_groups = self.selection_groups
        for group_index, group in enumerate(selection_groups):
            for index, points_area in enumerate(group.get_points_area()):
                x, y = [], []
                for corner in points_area:
                    x.append(corner.x)
                    y.append(corner.y)
                if (min(x) < cursor.x < max(x)) and (min(y) < cursor.y < max(y)):
                    window.cursor_modal_set('HAND')
                    self.in_area = 'POINT'
                    self.active_group = selection_groups[group_index]
                    group.index = index
                    if not group.is_center_origin:
                        group.origin = Vector(group.get_points()[index - 4])
                    return
            else:
                if group not in other_active:
                    group.origin = group.index = None
                elif group.last_index is not None:
                    group.index = group.last_index
                    if not group.is_center_origin:
                        group.origin = Vector(group.get_points()[group.index - 4])

        for group_index, group in enumerate(selection_groups):
            x, y = [], []
            for corner in group.corners:
                x.append(corner.x)
                y.append(corner.y) 
            if (min(x) < cursor.x < max(x)) and (min(y) < cursor.y < max(y)):
                window.cursor_modal_set('SCROLL_XY')
                self.in_area = 'CAGE'
                self.active_group = selection_groups[group_index]
                return

        self.in_area = False
        self.active_group = None
        window.cursor_modal_restore()

    def get_factor(self):
        active_group = self.active_group
        origin = active_group.origin
        rtv = bpy.context.region.view2d.region_to_view
        norm_init_cur_loc = Vector(rtv(*(self.init_cur_loc))) - origin
        norm_cursor_uv = Vector(rtv(*self.cursor)) - origin
        factor = Vector(norm_cursor_uv[i] / norm_init_cur_loc[i] for i in range(2))

        if (axis := active_group.CROSS.get(active_group.index)) is not None:
            if self.lock_aspect_ratio:
                factor = Vector((factor[axis], factor[axis]))
        else:
            if self.lock_aspect_ratio:
                factor = get_center(factor)
                factor = Vector((factor, factor))
            elif sum(self.axis) == 1:
                for index, axis in enumerate(self.axis):
                    if axis:
                        factor[1 - index] = 1
                        break
        self.scale_factor = factor
        return factor

    def get_offset(self):
        rtv = bpy.context.region.view2d.region_to_view
        offset = self.offset = Vector(rtv(*self.cursor)) - Vector(rtv(*self.init_cur_loc))
        if sum(self.axis) == 1:
            for index, axis in enumerate(self.axis):
                if axis:
                    offset[1 - index] = 0
                    break
        return offset

    def scale_selection_groups(self, factor=None):
        if not self.active_group.origin:  # Alternatingly spamming shift, click sometimes causes origin in this part to still be None
            return
        factor = factor if factor else self.get_factor()
        self.active_group.scale_uv(factor, self.lock_aspect_ratio)
        for other_group in self.other_active:
            other_group.scale_uv(factor, self.lock_aspect_ratio)

    def confirm(self, context, event):
        active_group = self.active_group
        other_active = self.other_active
        match self.in_area:
            case 'POINT':
                if event.ctrl:  # Toggles selection addition to other_active; For scaling multiple selections
                    if active_group in other_active:
                        if (active_group.index == active_group.last_index
                                and not event.shift):  # If not intending to change origin to center
                            other_active.remove(active_group)
                            active_group.last_index = None
                        else:
                            active_group.last_index = active_group.index
                    else:
                        other_active.add(active_group)
                        active_group.last_index = active_group.index

                    if event.shift:
                        active_group.origin = active_group.center
                        active_group.is_center_origin = True
                    else:
                        active_group.is_center_origin = False

                elif self.init_cur_loc:
                    self.init_cur_loc = None
                    groups = (active_group, *other_active)

                    undo_data = self.Action_uvVectors({group: group.uv_uvVectors for group in groups})
                    self.undo_stack.append(undo_data)
                    for group in groups:
                        group.replace_values()
                    undo_data.redo_groups_uv_uvVectors = {group: group.uv_uvVectors for group in groups}

                    self.scale_factor = [1, 1]
                    self.check_cursor_location(context)

            case 'CAGE' if self.init_cur_loc:
                self.init_cur_loc = None

                undo_data = self.Action_uvVectors({active_group: active_group.uv_uvVectors})
                self.undo_stack.append(undo_data)
                active_group.replace_values()
                undo_data.redo_groups_uv_uvVectors = {active_group: active_group.uv_uvVectors}

                self.offset = [0, 0]
                self.check_cursor_location(context)

    def cancel_current_action(self, context):
        self.init_cur_loc = None
        self.scale_factor = [1, 1]
        self.offset = [0, 0]
        active_group = self.active_group
        groups = (active_group, *self.other_active) if (self.in_area == 'POINT') else (active_group,)
        self.revert_uvVectors(groups=groups)

        context.window.cursor_modal_restore()
        self.check_cursor_location(context)
        self.set_header_text(context.area)

    def revert_uvVectors(self, groups=None, to_org=False):
        if groups is None:
            groups = self.selection_groups
        for group in groups:
            group.revert_uvVectors(to_org)

    def draw_widget(self):
        if self.is_widget_shown:
            state = gpu.state
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            shader.uniform_float("color", (1, 1, 1, 1))

            # vertices = []
            active = []
            points = []
            for group in self.selection_groups:
                ret = group.get_points_area()  # Recalculate group.vertices
                if ret is None:
                    self.error = "Not Edit Mode"
                    self.report({'ERROR'}, self.error)
                    return
                if not group.vertices:
                    raise NotImplementedError
                if (verts := group.active):
                    active.extend(verts)

                # vertices.extend(group.vertices)
                if group is self.active_group:
                    shader.uniform_float("color", (0, 1, 0, 1))

                lines = batch_for_shader(shader, 'LINES', {'pos': group.vertices})
                lines.draw(shader)
                shader.uniform_float("color", (1, 1, 1, 1))

                if (origin := group.origin):
                    points.append(origin)

            # lines = batch_for_shader(shader, 'LINES', {'pos': vertices})
            # lines.draw(shader)

            if active:
                lines = batch_for_shader(shader, 'LINES', {'pos': active})
                state.line_width_set(2)
                lines.draw(shader)
                state.line_width_set(1)

            if points:
                vtr = bpy.context.region.view2d.view_to_region
                points = [vtr(*point) for point in points]
                points = batch_for_shader(shader, 'POINTS', {'pos': points})
                state.point_size_set(self.POINT_SIZE)
                points.draw(shader)
                state.point_size_set(1)

        if getattr(self, "panel_shown", False):
            self.ui_layout.draw()


def register():
    bpy.utils.register_class(MXD_OT_UV_ScaleCage)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_ScaleCage)
