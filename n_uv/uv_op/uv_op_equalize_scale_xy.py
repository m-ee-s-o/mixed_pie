from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty
import bmesh
from .uv_utils import Base_UVOpsPoll, SearchUV, get_center_uvs, get_uvLayer_bmFaces


class MXD_OT_UV_EqualizeScaleXY(Base_UVOpsPoll, Operator):
    bl_idname = "uv.equalize_scale_xy"
    bl_label = "Equalize Island XY Scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Based on the dimensions of a selected island's bounding box, "                      \
                     "scale one of it's axis to match the other one.\n\n"                                 \
                     "Island Selection Mode: Instead of scaling an island based on just it's own axes, "  \
                     "it would now be based on all selected islands' axes"

    scale_shorter_axis: BoolProperty(name="Scale Shorter Axis", default=True)

    class Island():
        def __init__(self, indicesToLoops):
            self.indicesToLoops = indicesToLoops
            self.center, min_bounds, max_bounds = get_center_uvs(indicesToLoops.uvs, also_return_bounds=True)
            self.dimensions = (max_bounds.x - min_bounds.x, max_bounds.y - min_bounds.y)

    def invoke(self, context, event):
        objs = {context.object, *context.selected_objects}
        self.objsData_islands = defaultdict(list)
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
                    if uv_data.select:
                        loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, tuple(uv_data.uv), include_uvs=True)
                        loops_done.update(loops)
                        self.objsData_islands[data].append(self.Island(indicesToLoops))

        return self.execute(context)

    def execute(self, context):
        if context.scene.tool_settings.uv_select_mode != 'ISLAND':
            for data, islands in self.objsData_islands.items():
                uv_layer, bm_faces = get_uvLayer_bmFaces(data)

                for island in islands:
                    dimensions = island.dimensions
                    if dimensions[0] == dimensions[1]:
                        continue

                    index = 0 if (dimensions[0] < dimensions[1]) else 1
                    if not self.scale_shorter_axis:
                        index = 1 - index
                    scale_factor = dimensions[1 - index] / dimensions[index]
                    axis_center = island.center[index]

                    for uv, uvVectors in island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces).items():
                        norm_uv = uv[index] - axis_center
                        new_uv = norm_uv * scale_factor + axis_center

                        for uvVector in uvVectors:
                            uvVector[index] = new_uv

                bmesh.update_edit_mesh(data)
        else:
            islands = [island for islands in self.objsData_islands.values() for island in islands]
            func = max if self.scale_shorter_axis else min
            max_x = func(island.dimensions[0] for island in islands)
            max_y = func(island.dimensions[1] for island in islands)

            for data, islands in self.objsData_islands.items():
                uv_layer, bm_faces = get_uvLayer_bmFaces(data)

                for island in islands:
                    island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces, embed=True)
                    dimensions = island.dimensions

                    for index, max_ in enumerate((max_x, max_y)):
                        axis_dimension = dimensions[index]
                        if max_ == axis_dimension:
                            continue

                        scale_factor = max_ / axis_dimension
                        axis_center = island.center[index]

                        for uv, uvVectors in island.indicesToLoops.uv_uvVectors.items():
                            norm_uv = uv[index] - axis_center
                            new_uv = norm_uv * scale_factor + axis_center

                            for uvVector in uvVectors:
                                uvVector[index] = new_uv

                bmesh.update_edit_mesh(data)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_EqualizeScaleXY)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_EqualizeScaleXY)
