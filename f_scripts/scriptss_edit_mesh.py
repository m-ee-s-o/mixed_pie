import bpy
from bpy.types import Context, Event, Operator
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d
from ..m_edit.mesh.edit_mesh_ui import MXD_MT_PIE_EditMesh


class Origin_To_Selected:
    @classmethod
    def execute(cls, operator: Operator, context: Context):
        pre_cursor_location = context.scene.cursor.location.copy()

        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.object.mode_set(mode='EDIT')
        context.scene.cursor.location = pre_cursor_location


class Subdivide_Edge_And_Triangulate_Face_Above:
    """ Shift: Use the other face, instead of the one automatically selected. """

    pie_appendable_script = True

    @classmethod
    def invoke(cls, operator: Operator, context: Context, event: Event):
        if event.shift:
            operator.shift = True
        operator.append_to = MXD_MT_PIE_EditMesh.__name__
        operator.direction = "bottom"

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        me = context.object.data
        bm = bmesh.from_edit_mesh(me)

        selected_edges = []
        for edge in bm.edges:
            if edge.select:
                selected_edges.append(edge)

        faces = set()
        edge_face = {}

        for edge in selected_edges:
            faces_ys = []
            for face in edge.link_faces:
                ys = [location_3d_to_region_2d(context.region, context.space_data.region_3d, vert.co).y for vert in face.verts if vert not in edge.verts]
                faces_ys.append((face, max(ys)))
            
            sort = max if not getattr(operator, "shift", False) else min

            face = sort(faces_ys, key=lambda face_y: face_y[1])[0]
            if face not in faces:
                edge_face[edge] = face
                faces.add(face)

        for edge, face in edge_face.items():
            if face not in faces:
                continue
            vert_indices = {vert.index for vert in face.verts}

            bmesh.ops.subdivide_edges(bm, edges=[edge], cuts=1)

            center_vert = [vert for vert in face.verts if vert.index not in vert_indices][0]
            for edge in center_vert.link_edges:
                edge.select = True

            center_loop = [loop for loop in face.loops if loop.vert is center_vert][0]

            # If face is tri, make sure to only get one vertex (using set) as the 2 traversals below would point to the same vertex
            other_verts = {center_loop.link_loop_prev.link_loop_prev.vert, center_loop.link_loop_next.link_loop_next.vert}
            edges = (bm.edges.new((center_vert, vert)) for vert in other_verts)

            bmesh.utils.face_split_edgenet(face, edges)

        bmesh.update_edit_mesh(me)
    

class Branch_Out_Strand:
    """
    Used extruding hair strands.

    Shift: Use the other face, instead of the one automatically selected.
    
    """
    pie_appendable_script = True

    @classmethod
    def invoke(cls, operator: Operator, context: Context, event: Event):
        if event.shift:
            operator.shift = True
        operator.append_to = MXD_MT_PIE_EditMesh.__name__
        operator.direction = "left"

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        me = context.object.data
        bm = bmesh.from_edit_mesh(me)

        selected_edges = []
        for edge in bm.edges:
            if edge.select:
                selected_edges.append(edge)
        
        if len(selected_edges) != 1:
            operator.report({'WARNING'}, "Select only one edge.")
            return {'CANCELLED'}

        selected_edge = selected_edges[0]
        if not selected_edge.is_manifold:
            operator.report({'WARNING'}, "Non-manifold edge selected. Edge should have 2 faces connected.")
            return {'CANCELLED'}

        top_face = bottom_face = None
        faces_ys = []

        for face in selected_edge.link_faces:
            if len(face.loops) != 4:
                continue
            ys = [location_3d_to_region_2d(context.region, context.space_data.region_3d, vert.co).y for vert in face.verts if not vert.select]
            faces_ys.append((face, max(ys)))
        
        if len(faces_ys) != 2:
            operator.report({'WARNING'}, "Linked faces must be quad.")
            return {'CANCELLED'}

        if faces_ys[0][1] > faces_ys[1][1]:
            top_face = faces_ys[0][0]
            bottom_face = faces_ys[1][0]
        else:
            top_face = faces_ys[1][0]
            bottom_face = faces_ys[0][0]
        if getattr(operator, "shift", False):
            top_face, bottom_face = bottom_face, top_face
        
        crease_layer = bm.edges.layers.float[0]
        
        for face in (top_face, bottom_face):
            for loop in face.loops:
                if loop.edge is selected_edge:
                    loop.link_loop_prev.edge[crease_layer] = 1
                elif loop.link_loop_prev.edge is selected_edge:
                    loop.edge[crease_layer] = 1

        vert_indices = {vert.index for vert in top_face.verts}
        bmesh.ops.subdivide_edges(bm, edges=[selected_edge], cuts=1)

        # center_vert = next(iter(set(vert for vert in top_face.verts if not vert.select).intersection(vert for vert in bottom_face.verts if not vert.select)))
        center_vert = [vert for vert in top_face.verts if vert.index not in vert_indices][0]

        for vert in top_face.verts:
            vert.select = (vert is center_vert)

        bottom_verts = list(bottom_face.verts)
        bottom_verts.remove(center_vert)
        bm.faces.remove(bottom_face)
        bottom_face = bm.faces.new(bottom_verts, top_face)

        center_loop = center_vert.link_loops[0]
        bmesh.utils.face_split_edgenet(top_face, (bm.edges.new((center_loop.vert, center_loop.link_loop_next.link_loop_next.vert)),
                                                  bm.edges.new((center_loop.vert, center_loop.link_loop_prev.link_loop_prev.vert))))
        bmesh.update_edit_mesh(me)

        bpy.ops.mesh.select_mode()
        bpy.ops.transform.shrink_fatten('INVOKE_DEFAULT')


class Mark_Edges_Of_Strand_After_Extrude:
    pie_appendable_script = True

    @classmethod
    def invoke(cls, operator: Operator, context: Context, event: Event):
        operator.append_to = MXD_MT_PIE_EditMesh.__name__
        operator.direction = "bottom_left"

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        me = context.object.data
        bm = bmesh.from_edit_mesh(me)

        selected_vertices = []
        for vert in bm.verts:
            if vert.select:
                selected_vertices.append(vert)
        
        if len(selected_vertices) != 1:
            operator.report({'WARNING'}, "Select only one vertex.")
            return {'CANCELLED'}
        
        selected_vert = selected_vertices[0]
        left_right_verts = []
        loops = selected_vert.link_loops
        loops_amount = len(loops)

        if loops_amount != 5:
            operator.report({'WARNING'}, "Selected vertex must be linking 5 faces.")
            return {'CANCELLED'}
        
        # Carousel around the selected vertex
        order = []
        start = loops[0]
        for i in range(loops_amount):
            order.append(len(start.face.loops))
            start = start.link_loop_radial_next.link_loop_next

        for i in range(loops_amount):
            if order[i] == 4 \
                    and order[(i + 1) % loops_amount] == 4 \
                    and order[(i + 2) % loops_amount] == 3 \
                    and order[(i + 3) % loops_amount] == 3 \
                    and order[(i + 4) % loops_amount] == 3:
                break
        else:
            operator.report({'WARNING'}, "Selected vertex must be linking a 3 tris and two quads.")
            return {'CANCELLED'}

        for edge in selected_vert.link_edges:
            if len(edge.link_faces[0].verts) + len(edge.link_faces[1].verts) == 7:  # Edge is between a tri and quad
                left_right_verts.append(edge.other_vert(selected_vert))

        bottom_edge = None

        for edge in left_right_verts[0].link_edges:
            if edge.other_vert(left_right_verts[0]) is left_right_verts[1]:
                bottom_edge = edge

        if not bottom_edge:
            operator.report({'WARNING'}, "Vertices beside selected aren't connected.")
            return {'CANCELLED'}
        
        crease_layer = bm.edges.layers.float[0]

        bottom_edge.seam = True
        bottom_edge.smooth = False
        bottom_edge[crease_layer] = 1

        for edge in selected_vert.link_edges:
            if edge.other_vert(selected_vert) in left_right_verts:
                edge.seam = True
                edge[crease_layer] = 1

        left_right_edge = [None, None]
        
        for face in selected_vert.link_faces:
            if len(face.loops) == 4:
                loop = next(iter(set(face.loops).intersection(selected_vert.link_loops)))
                for i in range(4):
                    if loop.vert in left_right_verts:
                        if i == 1:
                            left_right_edge[0] = loop.edge

                            # Select edge loop below selected vert
                            nxt_vert = loop.link_loop_next.vert
                            for edge in nxt_vert.link_edges:
                                if (other_vert := edge.other_vert(nxt_vert)) is not loop.vert:
                                    other_vert.select = True
                                    edge.select = True
                            
                            nxt_nxt_vert = loop.link_loop_next.link_loop_next.vert
                            for edge in nxt_nxt_vert.link_edges:
                                if (other_vert := edge.other_vert(nxt_nxt_vert)) not in {selected_vert, nxt_vert}:
                                    edge.select = True

                            selected_vert.select = False
                            bm.select_history.add(nxt_nxt_vert)

                        elif i == 3:
                            left_right_edge[1] = loop.link_loop_prev.edge
                        break
                    loop = loop.link_loop_next

        for edge in left_right_edge:
            edge.smooth = False
            edge[crease_layer] = 1

        bmesh.update_edit_mesh(me)
