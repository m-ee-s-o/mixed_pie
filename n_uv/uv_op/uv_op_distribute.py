from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty, FloatVectorProperty
from mathutils import Vector
import bmesh
from .uv_utils import (
    Base_UVOpsPoll,
    SpaceBetweenIslands,
    SeriesIndicesToLoops,
    SearchUV,
    get_center_uvs,
    get_uvLayer_bmFaces,
)
from ...f_ui.utils_pie_menu import MXD_OT_Utils_PieMenu


class MXD_OT_UV_Distribute(Base_UVOpsPoll, SpaceBetweenIslands, MXD_OT_Utils_PieMenu, Operator):
    bl_idname = "uv.distribute"
    bl_label = "Distribute"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Distribute selected vertices.\n\n"                     \
                     "Island Selection Mode: Stack selected islands.\n"      \
                     "Shift: Stack selection in Vertex/Edge Selection Mode"

    def get_axis(self):
        return self.value_axis

    def set_axis(self, value):
        current_value = self.value_axis
        offset = self.value_offset
        if not all(current_value):
            if value[0] and not current_value[0]:
                offset[0] = offset[1]
            elif value[1] and not current_value[1]:
                offset[1] = offset[0]
        current_value[:] = value

    def get_offset(self):
        return self.value_offset

    def set_offset(self, value):
        self.value_offset = value
        if all(self.axis) and not self.offset_xy:
            self.value_offset[1] = self.value_offset[0]

    def update_offset_xy(self, context):
        if not self.offset_xy:
            self.value_offset[1] = self.value_offset[0]

    def get_invert(self):
        return (False, False)

    def set_invert(self, value):
        if value == (True, False):
            self.value_offset[0] *= -1
            if not self.offset_xy:
                self.value_offset[1] *= -1
        elif value == (False, True):
            self.value_offset[1] *= -1
    
    def set_toggle_island_axis(self, value):
        self.island_axis = 'X' if (self.island_axis == 'Y') else 'Y'

    _items_anchor = []
    def callback_anchor(self, context):
        _items_anchor = MXD_OT_UV_Distribute._items_anchor
        _items_anchor.clear()
        min, max = ("Leftmost", "Rightmost") if self.island_axis == 'X' else ("Bottommost", "Topmost")
        _items_anchor.append(('MIN', min, ""))
        _items_anchor.append(('MAX', max, ""))
        return _items_anchor

    axis: BoolVectorProperty(name="", size=2, subtype='XYZ', get=get_axis, set=set_axis)
    value_axis: BoolVectorProperty(size=2, default=(True, True))
    connected: BoolProperty(name="Connected", default=True,
                            description="If selection is an egde, vertices inside it will be distibuted base on the "
                                        "two endpoints' UV. If selection is a face or an edge with more than "
                                        "two endspoints, distribution will be based on the most outer vertices")
    select_shortest_path: BoolProperty(name="Fill Region",
                                       description='Use "Select Shortest Path" operator with "Fill Region" enabled')

    offset: FloatVectorProperty(name="", size=2, precision=3, min=-1, max=1, get=get_offset, set=set_offset,
                                description="Offset boundary")
    value_offset: FloatVectorProperty(size=2)
    offset_xy: BoolProperty(name="", update=update_offset_xy)
    invert: BoolVectorProperty(name="", description="Invert offset value", size=2,
                               get=get_invert, set=set_invert)
    
    align_y_to_nearest: BoolProperty(name="Align Y to Nearest")

    toggle_island_axis: BoolProperty(name="", set=set_toggle_island_axis)
    island_axis: EnumProperty(name="", items=[('X', "", ""), ('Y', "", "")])
    sort_by: EnumProperty(name="", items=[('LOCATION', "Location", ""), ('SIZE', "Size of Other Axis", "")], default='SIZE')
    center = ('CENTER', "Center", "")
    island_alignment_x: EnumProperty(name="Other Axis Alingment", items=[('LEFT', "Left", ""), center, ('RIGHT', "Right", "")], default='LEFT')
    island_alignment_y: EnumProperty(name="Other Axis Alingment", items=[('TOP', "Top", ""), center, ('BOTTOM', "Bottom", "")], default='TOP')

    is_ascending: BoolProperty(name="Ascending", default=True)
    anchor: EnumProperty(name="", items=callback_anchor)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        split = col.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        if self.stack:
            col1.label()
            col2.prop(self, "is_ascending")

            col1.separator(factor=0.5)
            col2.separator(factor=0.5)

            col1.label(text="Sort By")
            col2.prop(self, "sort_by")

            col1.separator()
            col2.separator()

            col1.label(text="Anchor")
            col2.prop(self, "anchor")

            col1.separator()
            col2.separator()

            s_col1 = col1.column(align=True)
            s_col1.alignment = 'RIGHT'

            s_col1.label(text=f"Islands Space: {self.island_axis}")
            row = col2.row()
            row.prop(self, "space_between_islands", index=0 if (self.island_axis == 'X') else 1)
            row.prop(self, "reset_space_between_islands", icon='FILE_REFRESH', emboss=False)

            col1.separator()
            col2.separator()                 

            col1.label(text="Stack Along Axis")
            row = col2.row(align=True)
            row.prop(self, "toggle_island_axis", text=self.island_axis, toggle=True)
            row.prop(self, f"island_alignment_{'y' if (self.island_axis == 'X') else 'x'}", text="")    

        else:
            if any(axis := self.axis):
                if not self.align_y_to_nearest:
                    offset_xy = self.offset_xy

                    col = col1.column(align=True)
                    col.alignment = 'RIGHT'

                    if offset_xy:  # Expanded
                        col.label(text="Offset: X")

                    row = col.row()
                    if all(axis):
                        row.prop(self, "offset_xy", emboss=False, icon_only=True, icon='TRIA_UP' if offset_xy else 'TRIA_RIGHT')  # Expand button

                    s_row = row.row()
                    s_row.alignment = 'RIGHT'
                    text = "XY" if not offset_xy and all(axis) else "Y" if axis[1] else "X"
                    if not offset_xy:
                        text = "Offset: " + text
                    s_row.label(text=text)         

                    col = col2.column(align=True)
                    for i in range(2):
                        if not (offset_xy or axis[i]):
                            continue
                        row = col.row()
                        row.enabled = (axis[i])
                        row.prop(self, "offset", index=i, slider=True)
                        row.prop(self, "invert", index=i, icon_only=True, icon='ARROW_LEFTRIGHT', emboss=False)
                        if not offset_xy:
                            break

                col1.separator(factor=0.25)
                col2.separator(factor=0.25)

                col1.label()
                col2.prop(self, "align_y_to_nearest")

                col1.label()
                col2.prop(self, "connected")

                col1.label()
                row = col2.row()
                row.enabled = (self.connected)
                row.prop(self, "select_shortest_path")

                col1.separator(factor=0.25)
                col2.separator(factor=0.25)

            col1.label(text="Axis")
            col2.row().prop(self, "axis", toggle=True)

    class SelectionGroup():
        def __init__(self, indicesToLoops, is_line):
            self.indicesToLoops = indicesToLoops
            self.is_line = is_line
            self.uvs_adjacent_y = {}

    class UnconnectedLoops():
        def __init__(self):
            self.indicesToLoops = SeriesIndicesToLoops()

    class Island():
        def __init__(self, indicesToLoops):
            self.indicesToLoops = indicesToLoops
            self.center, self.min_bounds, self.max_bounds = get_center_uvs(indicesToLoops.uvs, also_return_bounds=True)
            self.dimensions = self.max_bounds - self.min_bounds

        def set_origin(self, operator):
            self.origin = Vector((0, 0))

            match operator.island_axis:
                case 'X':
                    self.origin.x = self.min_bounds.x if (operator.anchor == 'MIN') else self.max_bounds.x
                    match operator.island_alignment_y:
                        case 'TOP':
                            self.origin.y = self.max_bounds.y
                        case 'CENTER':
                            self.origin.y = self.center.y
                        case 'BOTTOM':
                            self.origin.y = self.min_bounds.y
                case 'Y':
                    self.origin.y = self.min_bounds.y if (operator.anchor == 'MIN') else self.max_bounds.y
                    match operator.island_alignment_x:
                        case 'RIGHT':
                            self.origin.x = self.max_bounds.x
                        case 'CENTER':
                            self.origin.x = self.center.x
                        case 'LEFT':
                            self.origin.x = self.min_bounds.x

            self.space_from_origin_to_bounds = (self.max_bounds if (operator.anchor == 'MIN') else self.min_bounds) - self.origin

    def invoke(self, context, event):
        self.has_single_middle_vert = False
        self.objs = {context.object, *context.selected_objects}
        self.stack = context.scene.tool_settings.uv_select_mode == 'ISLAND' or event.shift

        if not self.stack:
            self.objsName_selectionGroups = defaultdict(list)
            self.objsName_unconnectedLoops = defaultdict(self.UnconnectedLoops)

            if self.select_shortest_path:
                bpy.ops.uv.shortest_path_select(use_fill=True)

            for obj in self.objs:
                bm = bmesh.from_edit_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.active
                loops_done = set()

                for vert in bm.verts:
                    if not vert.select:
                        continue
                    for loop in vert.link_loops:
                        if loop in loops_done:
                            continue
                        uv_data = loop[uv_layer]
                        uv = tuple(uv_data.uv)
                        if not uv_data.select:
                            continue
                        loops, indicesToLoops, is_line = SearchUV.connected_in_line_or_not(uv_layer, loop, uv)
                        loops_done.update(loops)

                        self.objsName_unconnectedLoops[obj.name].indicesToLoops.extend(indicesToLoops)
                        if is_line is None:
                            continue

                        uv_loops = defaultdict(list)
                        for loop in loops:
                            uv_loops[tuple(loop[uv_layer].uv)].append(loop)

                        if len(uv_loops) < 3:
                            continue

                        selection_group = self.SelectionGroup(indicesToLoops, is_line)

                        if is_line:
                            for uv, loops in tuple(uv_loops.items())[1: -1]:
                                y_s = []
                                for loop in loops:
                                    for adjacent_loop in (loop.link_loop_prev, loop.link_loop_next):
                                        uvVector = adjacent_loop[uv_layer].uv
                                        if tuple(uvVector) in uv_loops:
                                            continue
                                        y_s.append(uvVector.y)
                                
                                if y_s:
                                    y = min(y_s, key=lambda y: abs(y - uv[1]))
                                    selection_group.uvs_adjacent_y[uv] = y

                        self.objsName_selectionGroups[obj.name].append(selection_group)

            if len(self.objsName_selectionGroups) + len(self.objsName_unconnectedLoops) == 0:
                self.report({'INFO'}, "Selection not found.")
                return {'CANCELLED'}

            return self.execute(context)
        else:
            return self.invoke_pie_menu(context, event)

    def draw_structure(self, context, event, layout):
        layout.text_size *= 0.8
        layout.button('RIGHT_CENTER', "🡪", self.get_description)
        layout.button('RIGHT_TOP', "🡭", self.get_description)
        layout.button('TOP_RIGHT', "🡭", self.get_description)
        layout.button('TOP_CENTER', "🡩", self.get_description)
        layout.button('TOP_LEFT', "🡬", self.get_description)
        layout.button('LEFT_TOP', "🡬", self.get_description)
        layout.button('LEFT_CENTER', "🡨", self.get_description)
        layout.button('LEFT_BOTTOM', "🡯", self.get_description)
        layout.button('BOTTOM_LEFT', "🡯", self.get_description)
        layout.button('BOTTOM_CENTER', "🡫", self.get_description)
        layout.button('BOTTOM_RIGHT', "🡮", self.get_description)
        layout.button('RIGHT_BOTTOM', "🡮", self.get_description)

        layout.button_groups = (
            ('RIGHT_BOTTOM', 'RIGHT_CENTER', 'RIGHT_TOP'),
            ('TOP_RIGHT', 'TOP_CENTER', 'TOP_LEFT'),
            ('LEFT_TOP', 'LEFT_CENTER', 'LEFT_BOTTOM'),
            ('BOTTOM_LEFT', 'BOTTOM_CENTER', 'BOTTOM_RIGHT'),
        )

    @staticmethod
    def get_description(button):
        axis, alignment = button.id.split("_")
        button.island_axis = 'X' if (axis in {'LEFT', 'RIGHT'}) else 'Y'
        button.is_ascending = (axis in {'RIGHT', 'TOP'})
        button.anchor = 'MIN' if (axis in {'LEFT', 'BOTTOM'}) else 'MAX'

        if button.island_axis == 'X':
            button.island_alignment_y = alignment
        else:
            button.island_alignment_x = alignment

        return f"{button.island_axis} Axis\n"                                                                  \
               f"{'Ascending' if button.is_ascending else 'Descending'} order.\n"                              \
               f"{alignment.title()} {'Vertical' if (button.island_axis == 'X') else 'Horizontal'} Alignment"

    def button_effects(self, context, button):
        self.island_axis = button.island_axis
        self.is_ascending = button.is_ascending
        self.anchor = button.anchor

        if self.sort_by == 'LOCATION' and self.anchor != 'MAX':
            self.is_ascending = not self.is_ascending

        if hasattr(button, "island_alignment_y"):
            self.island_alignment_y = button.island_alignment_y
        else:
            self.island_alignment_x = button.island_alignment_x

        return self.invoke_stack(context)

    def invoke_stack(self, context):
        self.objsName_islands = defaultdict(list)
        for obj in self.objs:
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.active
            loops_done = set()

            for vert in bm.verts:
                if not vert.select:
                    continue
                for loop in vert.link_loops:
                    if loop in loops_done:
                        continue
                    uv_data = loop[uv_layer]
                    uv = tuple(uv_data.uv)
                    if not uv_data.select:
                        continue
                    loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, uv, active_only=True, include_uvs=True)
                    loops_done.update(loops)
                    self.objsName_islands[obj.name].append(self.Island(indicesToLoops))

        return self.execute(context)

    def execute(self, context):
        if not self.stack:
            if self.connected:
                for objName, selectionGroups in self.objsName_selectionGroups.items():
                    data = bpy.data.objects[objName].data
                    uv_layer, bm_faces = get_uvLayer_bmFaces(data)
                    for group in selectionGroups:
                        uv_uvVectors = group.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces)

                        if group.is_line:
                            uv_uvVectors_x = uv_uvVectors_y = uv_uvVectors
                        else:
                            uv_uvVectors_x = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[0])}
                            uv_uvVectors_y = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[1])}

                        self.modify_line(uv_uvVectors_x, uv_uvVectors_y, group.is_line, uvs_adjacentY=group.uvs_adjacent_y)

                    bmesh.update_edit_mesh(data)
            else:
                uv_uvVectors = defaultdict(list)
                objsData = []
                for objName, unconnectedLoops in self.objsName_unconnectedLoops.items():
                    data = bpy.data.objects[objName].data
                    objsData.append(data)
                    uv_layer, bm_faces = get_uvLayer_bmFaces(data)
                    for uv, uvVectors in unconnectedLoops.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces).items():
                        uv_uvVectors[uv].extend(uvVectors)

                uv_uvVectors_x = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[0])}
                uv_uvVectors_y = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[1])}

                self.modify_line(uv_uvVectors_x, uv_uvVectors_y, False)
                for data in objsData:
                    bmesh.update_edit_mesh(data)
            return {'FINISHED'}

        else:
            return self.stack_islands(context)

    def modify_line(self, uv_uvVectors_x, uv_uvVectors_y, is_line, uvs_adjacentY=None):
        offset = self.value_offset

        for i in range(2):
            if not self.axis[i]:
                continue
            if i == 0:
                uv_uvVectors = uv_uvVectors_x
            else:
                uv_uvVectors = uv_uvVectors_y

            if is_line:
                a_dict = uv_uvVectors
            else:
                a_dict = defaultdict(list)
                for uv, uvVectors in uv_uvVectors.items():
                    a_dict[uv[i]].extend(uvVectors)  # Group uvVectors that are aligned along an axis, treat them as one

            uvs = list(a_dict.keys())
            len_ = len(uvs)
            len_middle_verts = len_ - 2
            if len_middle_verts < 1:
                continue
            parts = len_middle_verts + 1

            is_not_ascending = (uvs[0][i] > uvs[-1][i]) if is_line else (uvs[0] > uvs[-1])
            if is_not_ascending:
                uvs.reverse()

            # Get boundaries which distance difference will serve as basis for increment
            boundaries = (uvs[0][i], uvs[-1][i]) if is_line else (uvs[0], uvs[-1])
            upper_bound = max(boundaries)
            lower_bound = min(boundaries)

            if is_line and self.align_y_to_nearest and i == 1:
                x1, y1 = uvs[-1]  # When i == 1 (y axis), uvs[-1] has the highest y
                x2, y2 = uvs[0]
                r_slope = (x2 - x1) / (y2 - y1)

                for uv in uvs[1: -1]:
                    y = uvs_adjacentY[uv]
                    x = x1 + (y - y1) * r_slope  # https://math.stackexchange.com/a/2297532

                    for uvVector in a_dict[uv]:
                        uvVector[:] = x, y

                return

            if offset[i]:
                # Offset boundaries: upper_bound downwards or lower_bound upwards

                if is_line and all(self.axis) and not self.offset_xy:
                    # This is so that when line is offset, points would "slide" both ways (/ and \) properly (would only normally work on one side)
                    if i == 0:
                        uvs_x = uvs
                    else:
                        same_signs = ((offset[0] > 0) == (offset[1] > 0))

                        # If the least x point is the greatest y, offset signs should be opposite, otherwise they should be the same
                        if uvs_x[0][1] > uvs_x[-1][1]:  
                            if same_signs:  # Only flip the sign if both are the same
                                offset[i] *= -1

                        elif not same_signs:
                            offset[i] *= -1

                offset_distance = (upper_bound - lower_bound) * abs(offset[i])

                if offset[i] > 0:
                    # If offset is towards right (greater than 0), points will visually go towards the upper_bound (lower_bound is offset towards upper_bound)
                    lower_bound += offset_distance
                elif offset[i] < 0:
                    upper_bound -= offset_distance

            distance = upper_bound - lower_bound
            increment = distance / parts
            for index, key in enumerate(uvs):
                if index not in {0, len_ - 1}:
                    new_uv = lower_bound + (increment * index)
                    for uvVector in a_dict[key]:
                        uvVector[i] = new_uv

                # #  Offset Visual
                #     continue
                # elif index == 0:
                #     new_uv = lower_bound
                # else:
                #     new_uv = upper_bound
                # for uvVector in a_dict[key]:
                #     uvVector[i] = new_uv
                #     break

    def stack_islands(self, context):
        islands = [island for islands in self.objsName_islands.values() for island in islands]
        if len(islands) < 2:
            self.report({'INFO'}, "There must be 2 or more selections.")
            return {'CANCELLED'}

        objsData = []
        for objName, obj_islands in self.objsName_islands.items():
            data = bpy.data.objects[objName].data
            objsData.append(data)
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)
            for island in obj_islands:
                island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces, embed=True)
                island.set_origin(self)

        i = 0 if (self.island_axis == 'X') else 1
        other = 1 - i

        starting_island = (min if (self.anchor == 'MIN') else max)(islands, key=lambda island: island.origin[i])
        starting_origin = starting_island.origin.copy()

        if self.sort_by == 'LOCATION':
            sorted_islands = sorted(islands, key=lambda island: island.origin[i])
        else:  # 'SIZE'
            sorted_islands = sorted(islands, key=lambda island: island.dimensions[other])

        space_between_islands = self.get_space_between_islands(context)[i]

        if self.anchor == 'MAX':
            # Since if anchor is 'MAX' (e.g., rightmost, topmost), starting from the starting origin,...
            # ...islands are stacked towards negative/'MIN' (e.g., leftmost, bottommost)
            space_between_islands *= -1  # So make the space negative to decrement
            sorted_islands.reverse()     # And since they're decrementing, reverse the islands so that the least island will be last and leftmost/bottommost

        if not self.is_ascending:
            sorted_islands.reverse()

        for island in sorted_islands:
            offset = starting_origin[i] - island.origin[i]

            for uvVectors in island.indicesToLoops.uv_uvVectors.values():
                for uvVector in uvVectors:
                    uvVector[i] += offset
                    uvVector[other] += starting_origin[other] - island.origin[other]
            
            starting_origin[i] += island.space_from_origin_to_bounds[i] + space_between_islands

        for data in objsData:
            bmesh.update_edit_mesh(data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_Distribute)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_Distribute)
