from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty, FloatVectorProperty
from mathutils import Vector
import bmesh
from .uv_utils import (
    Base_UVOpsPoll,
    IslandOffset,
    OrderedIndicesToLoops,
    SearchUV,
    get_center_uvs,
    get_uvLayer_bmFaces,
)
from ...f_ui.utils_pie_menu import MXD_OT_Utils_PieMenu


class MXD_OT_UV_Distribute(Base_UVOpsPoll, IslandOffset, MXD_OT_Utils_PieMenu, Operator):
    bl_idname = "uv.distribute"
    bl_label = "Distribute"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Distribute selected vertices.\n\n"                     \
                     "Island Selection Mode: Stack selected islands.\n"      \
                     "Shift: Stack selection in Vertex/Edge Selection Mode"

    def get_axis(self):
        return self.value_axis

    def set_axis(self, value):
        old_value = self.value_axis
        offset = self.value_offset
        if not all(old_value):
            if value[0] and not old_value[0]:
                offset[0] = offset[1]
            elif value[1] and not old_value[1]:
                offset[1] = offset[0]
        old_value[:] = value

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

    island_axis: BoolVectorProperty(name="", size=2, subtype='XYZ', default=(True, False))
    island_align: BoolProperty(name="Align Island", default=True)
    center = ('CENTER', "Center", "")
    island_alignment_x: EnumProperty(name="", items=[('LEFT', "Left", ""), center, ('RIGHT', "Right", "")], default='LEFT')
    island_alignment_y: EnumProperty(name="", items=[('TOP', "Top", ""), center, ('DOWN', "Down", "")], default='TOP')

    is_ascending: BoolProperty(name="Ascending", default=True, description="Use the closest island from 0 as origin")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        split = col.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        if self.stack:
            island_axis = self.island_axis

            if any(island_axis):
                if not all(island_axis):
                    if self.island_align:
                        for i in range(2):
                            i = 1 - i
                            if island_axis[i]:
                                if i == 1:
                                    col1.label(text="Align: X")
                                    col2.prop(self, "island_alignment_x")
                                else:
                                    col1.label(text="Align: Y" if (not island_axis[1 - i]) else "Y")
                                    col2.prop(self, "island_alignment_y")

                        col1.separator(factor=0.25)
                        col2.separator(factor=0.25)

                    col1.label(icon='BLANK1')
                    col2.row().prop(self, "island_align")

                col1.label(icon='BLANK1')
                col2.prop(self, "is_ascending")

                col1.separator(factor=0.25)
                col2.separator(factor=0.25)

                s_col1 = col1.column(align=True)
                s_col1.alignment = 'RIGHT'

                col = col2.column(align=True)
                for i in range(2):
                    if island_axis[i]:
                        row = col.row()
                        row.prop(self, "island_offset", index=i)
                        if i == 0:
                            s_col1.label(text="Offset: X")
                            row.prop(self, "reset_island_offset", icon='FILE_REFRESH', emboss=False)
                        else:
                            x_is_off = (not island_axis[1 - i])
                            s_col1.label(text="Offset: Y" if x_is_off else "Y")
                            if x_is_off:
                                row.prop(self, "reset_island_offset", icon='FILE_REFRESH', emboss=False)
                            else:
                                row.label(icon='BLANK1')

                col1.separator(factor=0.75)
                col2.separator(factor=0.75)

            col1.label(text="Stack Along Axis")
            col2.row().prop(self, "island_axis", toggle=True)
        else:
            if any(axis := self.axis):
                offset_xy = self.offset_xy

                col = col1.column(align=True)
                col.alignment = 'RIGHT'
                if offset_xy:
                    col.label(text="Offset: X")
                row = col.row()
                if all(axis):
                    row.prop(self, "offset_xy", emboss=False, icon_only=True,
                             icon='TRIA_UP' if offset_xy else 'TRIA_RIGHT')
                s_row = row.row()
                s_row.alignment = 'RIGHT'
                text = "XY" if not offset_xy and all(axis) else "Y" if axis[1] else "X"
                if not offset_xy:
                    text = "Offset: " + text
                s_row.label(text=text)         

                col1.label()
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
                col2.prop(self, "connected")
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

    class UnconnectedLoops():
        def __init__(self):
            self.indicesToLoops = OrderedIndicesToLoops()

    class Island():
        def __init__(self, indicesToLoops):
            self.indicesToLoops = indicesToLoops
            self.center, self.min_bounds, self.max_bounds = get_center_uvs(indicesToLoops.uvs, also_return_bounds=True)

        def set_origin(self, operator):
            origin = Vector((0, 0))
            center = self.center
            min_bounds = self.min_bounds
            max_bounds = self.max_bounds
            is_ascending = operator.is_ascending

            match tuple(operator.island_axis):
                case (True, False):  # X
                    origin.x = min_bounds.x if is_ascending else max_bounds.x
                    match operator.island_alignment_y:
                        case 'TOP':
                            origin.y = max_bounds.y
                        case 'CENTER':
                            origin.y = center.y
                        case 'DOWN':
                            origin.y = min_bounds.y

                case (False, True):  # Y
                    origin.y = min_bounds.y if is_ascending else max_bounds.y
                    match operator.island_alignment_x:
                        case 'RIGHT':
                            origin.x = max_bounds.x
                        case 'CENTER':
                            origin.x = center.x
                        case 'LEFT':
                            origin.x = min_bounds.x

                case (True, True):
                    origin[:] = min_bounds if is_ascending else max_bounds

            self.origin = origin
            self.padding = (max_bounds if is_ascending else min_bounds) - origin

    def invoke(self, context, event):
        self.objs = {context.object, *context.selected_objects}
        self.stack = True if event.shift else (context.scene.tool_settings.uv_select_mode == 'ISLAND')

        if not self.stack:
            self.objsData_selectionGroups = defaultdict(list)
            self.objsData_unconnectedLoops = defaultdict(self.UnconnectedLoops)

            if self.select_shortest_path:
                bpy.ops.uv.shortest_path_select(use_fill=True)

            for obj in self.objs:
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
                        uv = tuple(uv_data.uv)
                        if not uv_data.select:
                            continue
                        loops, indicesToLoops, is_line = SearchUV.connected_in_line_or_not(uv_layer, loop, uv)
                        loops_done.update(loops)
                        self.objsData_unconnectedLoops[data].indicesToLoops.extend(indicesToLoops)
                        if is_line is None:
                            continue
                        self.objsData_selectionGroups[data].append(self.SelectionGroup(indicesToLoops, is_line))

            if len(self.objsData_selectionGroups) + len(self.objsData_unconnectedLoops) == 0:
                self.report({'INFO'}, "Selection not found.")
                return {'CANCELLED'}

            return self.execute(context)
        else:
            return self.invoke_pie_menu(context, event)

    def draw_structure(self, context, event, layout):
        layout.button('RIGHT_CENTER', "🡪", self.__class__.get_description)
        layout.button('RIGHT_TOP', "🡭", self.__class__.get_description)
        layout.button('TOP_RIGHT', "🡭", self.__class__.get_description)
        layout.button('TOP_CENTER', "🡩", self.__class__.get_description)
        layout.button('TOP_LEFT', "🡬", self.__class__.get_description)
        layout.button('LEFT_TOP', "🡬", self.__class__.get_description)
        layout.button('LEFT_CENTER', "🡨", self.__class__.get_description)
        layout.button('LEFT_DOWN', "🡯", self.__class__.get_description)
        layout.button('DOWN_LEFT', "🡯", self.__class__.get_description)
        layout.button('DOWN_CENTER', "🡫", self.__class__.get_description)
        layout.button('DOWN_RIGHT', "🡮", self.__class__.get_description)
        layout.button('RIGHT_DOWN', "🡮", self.__class__.get_description)

        self.button_groups = (
            ('RIGHT_DOWN', 'RIGHT_CENTER', 'RIGHT_TOP'),
            ('TOP_RIGHT', 'TOP_CENTER', 'TOP_LEFT'),
            ('LEFT_TOP', 'LEFT_CENTER', 'LEFT_DOWN'),
            ('DOWN_LEFT', 'DOWN_CENTER', 'DOWN_RIGHT'),
        )

    @staticmethod
    def get_description(button):
        button.root.text_size *= 0.8
        axis, alignment = button.id.split("_")
        X, Y = (True, False), (False, True)
        button.island_axis = X if (axis in {'LEFT', 'RIGHT'}) else Y
        button.is_ascending = (axis in {'LEFT', 'DOWN'})
        if button.island_axis == X:
            button.island_alignment_y = alignment
        else:
            button.island_alignment_x = alignment
        return f"{'X' if button.island_axis == X else 'Y'}\n"  \
               f"{'Ascending' if button.is_ascending else 'Descending'} based on an island's {axis.lower()}most vertex\n"                 \
               f"{alignment.title()} {'Vertical' if button.island_axis == X else 'Horizontal'} Alignment"

    def button_effects(self, context, button):
        self.island_align = True
        self.island_axis = button.island_axis
        self.is_ascending = button.is_ascending
        if hasattr(button, "island_alignment_y"):
            self.island_alignment_y = button.island_alignment_y
        else:
            self.island_alignment_x = button.island_alignment_x

        return self.invoke_stack(context)

    def invoke_stack(self, context):
        self.objsData_islands = defaultdict(list)
        for obj in self.objs:
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
                    uv = tuple(uv_data.uv)
                    if not uv_data.select:
                        continue
                    loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, uv, active_only=True, include_uvs=True)
                    loops_done.update(loops)
                    self.objsData_islands[data].append(self.Island(indicesToLoops))

        return self.execute(context)

    def execute(self, context):
        if not self.stack:
            if self.connected:
                for data, selectionGroups in self.objsData_selectionGroups.items():
                    uv_layer, bm_faces = get_uvLayer_bmFaces(data)
                    for group in selectionGroups:
                        uv_uvVectors = group.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces)

                        if group.is_line:
                            uv_uvVectors_x = uv_uvVectors_y = uv_uvVectors
                        else:
                            uv_uvVectors_x = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[0])}
                            uv_uvVectors_y = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[1])}

                        self.modify_line(uv_uvVectors_x, uv_uvVectors_y, group.is_line)

                    bmesh.update_edit_mesh(data)
            else:
                uv_uvVectors = defaultdict(list)
                for data, unconnectedLoops in self.objsData_unconnectedLoops.items():
                    uv_layer, bm_faces = get_uvLayer_bmFaces(data)
                    for uv, uvVectors in unconnectedLoops.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces).items():
                        uv_uvVectors[uv].extend(uvVectors)

                uv_uvVectors_x = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[0])}
                uv_uvVectors_y = {uv: uv_uvVectors[uv] for uv in sorted(uv_uvVectors, key=lambda uv: uv[1])}

                self.modify_line(uv_uvVectors_x, uv_uvVectors_y, False)
                for data in self.objsData_unconnectedLoops:
                    bmesh.update_edit_mesh(data)
            return {'FINISHED'}

        elif any(self.island_axis):
            return self.stack_islands(context)

        return {'CANCELLED'}

    def modify_line(self, uv_uvVectors_x, uv_uvVectors_y, is_line):
        offset = self.offset
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

            # This is so that when line is offset, it would "slide" both ways (/ and \) properly (would only normally work on one side)
            reverse = False
            if is_line and all(self.axis):
                if i == 1:
                    if uvs_x[0][1] > uvs_x[-1][1]:
                        # If the least x point is the greatest y, offset signs should be opposite, otherwise same
                        reverse = True
                else:
                    uvs_x = uvs

            boundaries = (uvs[0][i], uvs[-1][i]) if is_line else (uvs[0], uvs[-1])
            upper_bound = max(boundaries)
            lower_bound = min(boundaries)

            if (i == 1) and all(self.axis) and not self.offset_xy:
                x_greater = (offset[0] > 0)
                y_greater = (offset[1] > 0)
                same_signs = (x_greater - y_greater == 0)

                if reverse:
                    if same_signs:  # Only flip the sign if both are the same
                        offset[i] *= -1
                elif not same_signs:
                        offset[i] *= -1

            offset_factor = 1 - abs(offset[i])
            offset_distance = (upper_bound - lower_bound) * offset_factor

            if offset[i] > 0:
                lower_bound = upper_bound - offset_distance
            elif offset[i] < 0:
                upper_bound = lower_bound + offset_distance

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
        # TODO: Make self.island_axis enumProp, removing not not(all) and all
        islands = [island for islands in self.objsData_islands.values() for island in islands]
        if len(islands) < 2:
            self.report({'INFO'}, "There must be 2 or more selections.")
            return {'CANCELLED'}

        island_offset = self.get_island_offset(context)
        if not self.is_ascending:
            island_offset *= -1

        for data, obj_islands in self.objsData_islands.items():
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)
            for island in obj_islands:
                island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces, embed=True)
                island.set_origin(self)

        for i in range(2):
            if not self.island_axis[i]:
                continue
            other = 1 - i

            sorted_islands = sorted(islands, key=lambda island: island.origin[i], reverse=(not self.is_ascending))
            basis_origin = list(sorted_islands[0].origin)
            for index, island in enumerate(sorted_islands):
                padding = island.padding[i]
                if index != 0:
                    offset = basis_origin[i] - island.origin[i]

                    for uvVectors in island.indicesToLoops.uv_uvVectors.values():
                        for uvVector in uvVectors:
                            uvVector[i] += offset
                            if self.island_align and not self.island_axis[other]:
                                uvVector[other] += basis_origin[other] - island.origin[other]

                basis_origin[i] += padding + island_offset[i]

        for data in self.objsData_islands.keys():
            bmesh.update_edit_mesh(data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_Distribute)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_Distribute)
