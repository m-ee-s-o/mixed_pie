from collections import defaultdict
from math import cos, radians, sin
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
import bmesh
from mathutils import Matrix, Vector
from .uv_utils import (
    Base_UVOpsPoll,
    SeriesIndicesToLoops,
    SearchUV,
    get_center_uvs,
    get_uvLayer_bmFaces,
)


class MXD_OT_UV_ToCirlce(Base_UVOpsPoll, Operator):
    bl_idname = "uv.to_circle"
    bl_label = "UV to Circle"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Turn selected edge loop(s) into circle. If selection is not an edge loop, "  \
                     "search every edge loops in its island outside of the selection "             \
                     "(useful when the whole island is circular, just select the center)"

    force_apply_to_island: BoolProperty(
        name="Force Apply to Island",
        description="When operating on a whole island is desired but the center is a face, "
                    "instead of turning only that face's edge loop into a circle, "
                    "enable this option to forcibly affect the whole island",
    )
    active_as_center: BoolProperty(
        name="Active as Center",
        description="Use an island's active selection as the center for every circles that its edge loops would turn into",
        default=True,
    )

    class EdgeLoop:
        def __init__(self, loop_uv: dict, active_loops: dict):
            """
            Parameters:
                loop_uv: {loop: uv,...} --- Ordered loops in an edge loop.
                active_loops --- Same as loop_uv but are the active loops before operation.
            """

            self.center = get_center_uvs(loop_uv.values())
            self.center_of_active = get_center_uvs(active_loops.values())
            self.indicesToLoops = SeriesIndicesToLoops()
            self.indicesToLoops.bulk_construct(loop_uv)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row()
        row.enabled = (self.force_apply_to_island_enabled)
        row.prop(self, "force_apply_to_island")

        row = layout.row()
        row.enabled = (self.active_as_center_enabled)
        row.prop(self, "active_as_center")

    def invoke(self, context, event):
        has_edge_loop_in_selection = False
        has_islands = False
        
        objs = {context.object, *context.selected_objects}
        self.objData_edgeLoops = defaultdict(list)
        self.objData_edgeLoops_forceApply = defaultdict(list)
        for obj in objs:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active

            pre_active_loops = set()
            loops_done = set()
            # When appending to to_search_islands, uv shouldn't be added to loops_done since...
            # ...in self.search_island_edge_loops, the uv shouldn't be in loops_done
            loops_done_2 = set()
            to_search_islands = []
            to_search_islands_forceApply = []

            for vert in bm.verts:
                if not vert.select:
                    continue
                for loop in vert.link_loops:
                    if loop in loops_done or loop in loops_done_2:
                        continue
                    uv_data = loop[uv_layer]
                    uv = tuple(uv_data.uv)
                    if uv_data.select:
                        loop_uv, looped = SearchUV.connected_in_same_active_edge_loop(uv_layer, loop, uv)
                        pre_active_loops.update(loop_uv)

                        if looped:
                            to_search_islands_forceApply.append({'loop_m': loop, 'uv_m': uv, 'active_loops': loop_uv})
                            loops_done_2.update(loop_uv)

                            self.objData_edgeLoops[data].append(self.EdgeLoop(loop_uv, loop_uv))
                            has_edge_loop_in_selection = True
                        else:
                            to_search_islands.append({'loop_m': loop, 'uv_m': uv, 'active_loops': loop_uv})
                            loops_done_2.update(loop_uv)

            if to_search_islands:
                has_islands = True
                for loop_uv, active_loops in SearchUV.search_island_edge_loops(uv_layer, pre_active_loops, loops_done, to_search_islands):
                    self.objData_edgeLoops[data].append(self.EdgeLoop(loop_uv, active_loops))
            
            if to_search_islands_forceApply:
                has_islands = True
                for loop_uv, active_loops in SearchUV.search_island_edge_loops(uv_layer, pre_active_loops, loops_done, to_search_islands_forceApply):
                    self.objData_edgeLoops_forceApply[data].append(self.EdgeLoop(loop_uv, active_loops))

        if not self.objData_edgeLoops:
            return {'CANCELLED'}

        self.force_apply_to_island_enabled = has_edge_loop_in_selection
        self.active_as_center_enabled = has_islands

        return self.execute(context)

    def execute(self, context):
        dicts = (self.objData_edgeLoops, self.objData_edgeLoops_forceApply) if self.force_apply_to_island else (self.objData_edgeLoops,)
        objData_edgeLoops = defaultdict(list)
        for dict in dicts:
            for data, edgeLoops in dict.items():
                objData_edgeLoops[data].extend(edgeLoops)

        zeroAngleVector = Vector((10, 0))

        for data, edgeLoops in objData_edgeLoops.items():
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)

            for edgeLoop in edgeLoops:
                uv_uvVectors = edgeLoop.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces)
                center = edgeLoop.center

                if self.active_as_center:
                    copy_uv_uvVectors = uv_uvVectors.copy()
                    uv_uvVectors.clear()
                    offset = edgeLoop.center_of_active - center
                    for uv, uvVectors in copy_uv_uvVectors.items():
                        for uvVector in uvVectors:
                            uvVector[:] = uvVector + offset
                        uv_uvVectors[tuple(Vector(uv) + offset)].extend(uvVectors)
                    center = edgeLoop.center_of_active

                longest_axis_length = 0  # Get longest axis length and uv (key)
                angle_closest_to_0 = (3.15, 0, (None)) # Abs(Angle), Angle, UV (key)
                for uv in uv_uvVectors:
                    norm_uv = Vector(uv) - center
                    for i in norm_uv:
                        abs_norm_uv = abs(i)
                        if abs_norm_uv > longest_axis_length:
                            longest_axis_length = abs_norm_uv

                    angle = norm_uv.angle_signed(zeroAngleVector)
                    abs_angle = abs(angle)
                    if abs_angle < angle_closest_to_0[0]:
                        angle_closest_to_0 = (abs_angle, angle, uv)

                order = [uv for uv in uv_uvVectors]
                index = order.index(angle_closest_to_0[2])
                order = order[index + 1:] + order[:index]

                start_angle = angle_closest_to_0[1]
                starting_norm_uv = Vector((longest_axis_length * cos(start_angle), longest_axis_length * sin(start_angle)))
                starting_norm_uv.rotate(Matrix.Rotation(start_angle * -1, 2))
                for uvVector in uv_uvVectors[angle_closest_to_0[2]]:
                    uvVector[:] = starting_norm_uv + center

                increment = 360 / len(uv_uvVectors)
                mat_rotation = Matrix.Rotation(radians(increment), 2)
                cur_norm_uv = starting_norm_uv
                for uv in order:
                    cur_norm_uv = mat_rotation @ Vector(cur_norm_uv)
                    for uvVector in uv_uvVectors[uv]:
                        uvVector[:] = cur_norm_uv + center

            bmesh.update_edit_mesh(data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_ToCirlce)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_ToCirlce)
