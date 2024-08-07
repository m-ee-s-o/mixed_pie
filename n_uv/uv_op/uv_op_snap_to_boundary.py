from collections import defaultdict
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty
import bmesh
from mathutils import Vector
from .uv_utils import Base_UVOpsPoll, IndicesToLoops, SpaceBetweenIslands, get_center_uvs, get_uvLayer_bmFaces, set_uv_uvVectors


class MXD_OT_UV_SnapToBoundary(Base_UVOpsPoll, SpaceBetweenIslands, Operator):
    bl_idname = "uv.snap_to_boundary"
    bl_label = "Snap To Boundary"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Snap selection to a bound point"

    bound_points = {
            'TOP_LEFT' : (0, 1),
                 'TOP' : (0.5, 1),
           'TOP_RIGHT' : (1, 1),
                'LEFT' : (0, 0.5),
               'RIGHT' : (1, 0.5),
         'BOTTOM_LEFT' : (0, 0),
              'BOTTOM' : (0.5, 0),
        'BOTTOM_RIGHT' : (1, 0),
    }

    direction: EnumProperty(items=[(direction, direction.replace("_", " ").title(), "")
                                   for direction in bound_points],
                            name="")
    snap_to_center: BoolProperty(name="Snap To Center", default=True)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        split = col.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        if self.direction in {'TOP', 'BOTTOM', 'RIGHT', 'LEFT'}:
            col1.label()
            col2.prop(self, "snap_to_center")

        col1.label(text="Direction")
        col2.prop(self, "direction")

        col1.separator(factor=0.25)
        col2.separator(factor=0.25)

        col1.label(text="Offset")
        row = col2.row()
        row.column().prop(self, "space_between_islands")
        row.prop(self, "reset_space_between_islands", icon='FILE_REFRESH', emboss=False)

    def invoke(self, context, event):
        objs = {context.object, *context.selected_objects}
        self.objName_indicesToLoops = {}
        for obj in objs:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            indicesToLoops = IndicesToLoops()

            for vert in bm.verts:
                if not vert.select:
                    continue
                for loop in vert.link_loops:
                    uv_data = loop[uv_layer]
                    if uv_data.select:
                        indicesToLoops.construct(loop)

            if indicesToLoops:
                self.objName_indicesToLoops[obj.name] = indicesToLoops

        return self.execute(context) if self.objName_indicesToLoops else {'CANCELLED'}

    def execute(self, context):
        objName_uv_uvVectors = {}
        for objName, indicesToLoops in self.objName_indicesToLoops.items():
            data = bpy.data.objects[objName].data
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)
            objName_uv_uvVectors[objName] = defaultdict(list)
            set_uv_uvVectors(uv_layer, bm_faces, objName_uv_uvVectors[objName], indicesToLoops)

        uvs = [uv for uv_uvVectors in objName_uv_uvVectors.values() for uv in uv_uvVectors]
        center, min_bounds, max_bounds = get_center_uvs(uvs, also_return_bounds=True)

        direction = self.direction
        bound_point_uv = Vector(self.bound_points[direction])
        match direction:
            case 'TOP_LEFT':
                origin = (min_bounds.x, max_bounds.y)
            case 'TOP':
                origin = (center.x, max_bounds.y)
            case 'TOP_RIGHT':
                origin = (max_bounds.x, max_bounds.y)
            case 'LEFT':
                origin = (min_bounds.x, center.y)
            case 'RIGHT':
                origin = (max_bounds.x, center.y)
            case 'BOTTOM_LEFT':
                origin = (min_bounds.x, min_bounds.y)
            case 'BOTTOM':
                origin = (center.x, min_bounds.y)
            case 'BOTTOM_RIGHT':
                origin = (max_bounds.x, min_bounds.y)

        space_between_island_and_bound = self.get_space_between_islands(context, uv_bounds=True)
        for i in range(2):
            if bound_point_uv[i] == 1:
                space_between_island_and_bound[i] *= -1

        offset = bound_point_uv - Vector(origin) + space_between_island_and_bound
        if not self.snap_to_center:
            match direction:
                case 'TOP' | 'BOTTOM':
                    offset[0] = 0
                case 'RIGHT' | 'LEFT':
                    offset[1] = 0

        for objName, uv_uvVectors in objName_uv_uvVectors.items():
            data = bpy.data.objects[objName].data
            for uv, uvVectors in uv_uvVectors.items():
                new_uv = Vector(uv) + offset
                for uvVector in uvVectors:
                    uvVector[:] = new_uv

            bmesh.update_edit_mesh(data)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MXD_OT_UV_SnapToBoundary)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_SnapToBoundary)
