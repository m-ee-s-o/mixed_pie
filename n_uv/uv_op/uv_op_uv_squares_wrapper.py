from collections import defaultdict
import bpy
from bpy.types import Operator
import bmesh
from .uv_utils import Base_UVOpsPoll, IndicesToLoops
from addon_utils import check


class MXD_OT_UV_UVSquaresWrapper(Base_UVOpsPoll, Operator):
    bl_idname = "uv.uv_squares_wrapper"
    bl_label = "UV Squares Wrapper"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Wrapper for UV Squares to do custom operations after"

    @classmethod
    def poll(self, context):
        return check("UvSquares-master") == (True, True)

    def invoke(self, context, event):
        objsData___uvs_indicesToLoops = {}
        for obj in {context.object, *context.selected_objects}:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            loops_done = set()
            uvs_indicesToLoops = defaultdict(list)

            for vert in bm.verts:
                if not vert.select:
                    continue
                for loop in vert.link_loops:
                    if loop in loops_done:
                        continue
                    uv_data = loop[uv_layer]
                    if uv_data.select:
                        uvs_indicesToLoops[tuple(uv_data.uv)].append(IndicesToLoops.getIndicesToLoop(loop))

            if uvs_indicesToLoops:
                objsData___uvs_indicesToLoops[data] = uvs_indicesToLoops

            bm.free()

        if not objsData___uvs_indicesToLoops:
            return {'CANCELLED'}
        
        bpy.ops.uv.uv_squares_by_shape()

        for obj_data, uvs_indicesToLoops in objsData___uvs_indicesToLoops.items():
            bm = bmesh.from_edit_mesh(obj_data)
            uv_layer = bm.loops.layers.uv.active
            
            for _, indicesToLoops in uvs_indicesToLoops.items():
                uv_data = []

                for face_index, face_loop_index in indicesToLoops:
                    uv_data.append(bm.faces[face_index].loops[face_loop_index][uv_layer])
                
                if len(set(tuple(data.uv) for data in uv_data)) != 1:
                    x = max(uv_data, key=lambda data: data.uv.x).uv.x
                    y = max(uv_data, key=lambda data: data.uv.y).uv.y
                    for data in uv_data:
                        data.uv = (x, y)
                        data.pin_uv = True
            
            bmesh.update_edit_mesh(obj_data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_UVSquaresWrapper)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_UVSquaresWrapper)
