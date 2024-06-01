from collections import defaultdict
from math import atan2, degrees, radians
import bpy
from bpy.types import Operator
from bpy.props import EnumProperty
import bmesh
from mathutils import Matrix, Vector
from .uv_utils import Base_UVOpsPoll, SearchUV, get_uvLayer_bmFaces


class MXD_OT_UV_AlignEdgeRotateIsland(Base_UVOpsPoll, Operator):
    bl_idname = "uv.align_edge_rotate_island"
    bl_label = "Align Edge, Rotate Island"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Rotates an edge so that it aligns parallel to an axis, then rotate its island with it"

    mode: EnumProperty(items=(('AUTO', "Auto", ""),
                              ('X', "X", ""),
                              ('Y', "Y", "")),
                       name="Mode")

    class Island():
        def __init__(self, indicesToLoops, active_uvs):
            self.indicesToLoops = indicesToLoops
            self.active_uvs = active_uvs

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        col1.label(text="Mode")
        col2.prop(self, "mode", text="")
        if self.ignored_islands:
            col1.separator(factor=0.25)
            col1.label(text="Ignored Islands")
            col2.separator(factor=0.25)
            row = col2.row()
            row.label(text=f"{self.ignored_islands}")
            s_row = row.row()
            op = s_row.operator("utils.properties_toggle_description", emboss=False, icon='INFO')
            op.description = "Islands with more or less than one edge selected are ignored"

    def invoke(self, context, event):
        self.ignored_islands = 0
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
                    uv1 = tuple(uv_data.uv)
                    uv2 = tuple(loop.link_loop_next[uv_layer].uv)
                    if uv_data.select_edge:
                        loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, uv1, active_uvs=(uv1, uv2), include_uvs=True)
                        ignore = False
                        if "ignore_island" in indicesToLoops:
                            ignore = True
                            del indicesToLoops['ignore_island']
                            self.ignored_islands += 1
                        loops_done.update(loops)
                        if ignore:
                            continue
                        self.objsData_islands[data].append(self.Island(indicesToLoops, active_uvs=(uv1, uv2)))

        return self.execute(context)

    def execute(self, context):
        for data, islands in self.objsData_islands.items():
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)

            for island in islands:
                uv1, uv2 = island.active_uvs
                if uv1[1] < uv2[1]:  # Always make uv1's y be the one above 0, only 0-180 degrees are implemented
                    uv1, uv2 = uv2, uv1

                center = ((uv1[0] + uv2[0]) / 2, (uv1[1] + uv2[1]) / 2)
                init_angle = degrees(atan2(uv1[1] - center[1], uv1[0] - center[0]))

                match self.mode:
                    case 'AUTO':
                        if 135 > init_angle > 45:            # Align parallel to y axis
                            target_angle = 90 - init_angle
                        elif init_angle <= 45:               # Else, align parallel to x axis
                            target_angle = -init_angle
                        elif init_angle >= 135:
                            target_angle = 180 - init_angle
                    case 'X':
                        if init_angle <= 90:
                            target_angle = -init_angle
                        else:
                            target_angle = 180 - init_angle
                    case 'Y':
                        target_angle = 90 - init_angle

                mat_rotation = Matrix.Rotation(radians(target_angle), 2)
                for uv, uvs in island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces).items():
                    xy = (uv[0] - center[0], uv[1] - center[1])
                    new_xy = mat_rotation @ Vector(xy)
                    for i in range(2):
                        for uv in uvs:
                            uv[i] = new_xy[i] + center[i]

            bmesh.update_edit_mesh(data)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_AlignEdgeRotateIsland)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_AlignEdgeRotateIsland)
