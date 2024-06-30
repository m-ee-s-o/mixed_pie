from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import EnumProperty
import bmesh
from .uv_utils import Base_UVOpsPoll, SpaceBetweenIslands, SearchUV, get_uvLayer_bmFaces


class MXD_OT_UV_AlignVerticesMoveIslands(Base_UVOpsPoll, SpaceBetweenIslands, Operator):
    bl_idname = "uv.align_vertices_move_islands"
    bl_label = "Align Vertices, Move Islands"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""

    direction: EnumProperty(items=[('TOP', "Top", ""), ('BOTTOM', "Bottom", ""),
                                   ('RIGHT', "Right", ""), ('LEFT', "Left", "")],
                            name="", description="Use the farthest island in this direction as origin")

    class Island():
        def __init__(self, indicesToLoops, uv_of_active):
            self.indicesToLoops = indicesToLoops
            self.uv_of_active = uv_of_active

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        split = col.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        col1.label(text="Origin")
        col2.prop(self, "direction")

        col1.separator(factor=0.25)
        col2.separator(factor=0.25)

        col1.label(text=f"Islands Space: {'X' if (self.axis == 0) else 'Y'}")
        row = col2.row()
        row.prop(self, "space_between_islands", index=self.axis)
        row.prop(self, "reset_space_between_islands", icon='FILE_REFRESH', emboss=False)

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
                        uv = tuple(uv_data.uv)
                        loops, indicesToLoops = SearchUV.connected_in_same_island(uv_layer, loop, uv, active_uvs=(uv,))
                        if "ignore_island" in indicesToLoops:
                            self.report({'INFO'}, "There shouldn't be two active uvs in an island.")
                            return {'CANCELLED'}
                        loops_done.update(loops)
                        self.objsData_islands[data].append(self.Island(indicesToLoops, uv))

        if len([island for islands in self.objsData_islands.values() for island in islands]) < 2:
            self.report({'INFO'}, "Select two or more vertices from different islands.")
            return {'CANCELLED'}

        return self.execute(context)

    def execute(self, context):
        direction = self.direction
        space_between_islands = self.get_space_between_islands(context)
        if direction in {'TOP', 'RIGHT'}:
            space_between_islands *= -1

        islands = [island for islands in self.objsData_islands.values() for island in islands]
        match direction:
            case 'TOP':
                origin_island = max(islands, key=lambda island: island.uv_of_active[1])
            case 'BOTTOM':
                origin_island = min(islands, key=lambda island: island.uv_of_active[1])
            case 'RIGHT':
                origin_island = max(islands, key=lambda island: island.uv_of_active[0])
            case 'LEFT':
                origin_island = min(islands, key=lambda island: island.uv_of_active[0])
        self.axis = axis = 1 if direction in {'TOP', 'BOTTOM'} else 0

        for data, islands in self.objsData_islands.items():
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)

            for island in islands:
                if island is origin_island:
                    continue

                offset = origin_island.uv_of_active[axis] - island.uv_of_active[axis] + space_between_islands[axis]

                for uvVectors in island.indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces).values():
                    for uvVector in uvVectors:
                        uvVector[axis] += offset

            bmesh.update_edit_mesh(data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_AlignVerticesMoveIslands)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_AlignVerticesMoveIslands)
