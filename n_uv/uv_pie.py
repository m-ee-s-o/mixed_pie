from math import radians
import bpy
from bpy.types import Menu


class MXD_MT_PIE_UVEditor(Menu):
    bl_label = "UV Editor"

    def draw(self, context):
        tool_settings = context.scene.tool_settings
        snap = tool_settings.use_snap_uv
        uv_sync_sel = tool_settings.use_uv_select_sync
        proportional_editing = tool_settings.use_proportional_edit

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.call_menu_pie", text="Snap To Border",                                      # Left
                     icon='BLANK1').name = "MXD_MT_PIE_UVEditor_SnapToBoundary"
        pie.operator("wm.call_menu_pie", text="Align Vertices, Move Islands",                        # Right
                     icon='BLANK1').name = "MXD_MT_PIE_UVEditor_AlignVerticesMoveIslands"

        op = pie.operator("uv.align_rotation", icon='BLANK1')                                        # Bottom
        op.method = 'GEOMETRY'
        op.axis = 'Z'

        pie.operator("uv.use_snap", depress=(snap),                                                  # Top
                     icon='CHECKBOX_HLT' if snap else 'CHECKBOX_DEHLT')
        pie.operator("wm.context_toggle", depress=(uv_sync_sel),                                     # Top_left
                     icon='CHECKBOX_HLT' if uv_sync_sel else 'CHECKBOX_DEHLT',
                     text="UV Sync Selection").data_path = "scene.tool_settings.use_uv_select_sync"
        pie.operator("edit.tool_settings", depress=(proportional_editing),                           # Top_right
                     icon='CHECKBOX_HLT' if proportional_editing else 'CHECKBOX_DEHLT',
                     text="Proportional Editing").mode = 'PROPORTIONAL_EDITING'
        pie.operator("uv.to_circle", icon='BLANK1')                                                  # Bottom_left
        pie.operator("uv.average_islands_scale", icon='BLANK1')                                      # Bottom_right


class MXD_MT_PIE_UVEditor_MarkEgde(Menu):
    bl_label = "UV Editor, Mark Edge"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator_context = 'EXEC_DEFAULT'  # Only calls op.execute, skipping any modal

        pie.operator("uv.mark_seam", text="Clear Seam", icon='BLANK1').clear = True           # Left
        pie.operator("uv.mark_seam", icon='BLANK1')                                           # Right
        pie.separator()  # Bottom
        pie.separator()  # Top
        pie.separator()  # Top_left
        pie.separator()  # Top_right
        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


class MXD_MT_PIE_UVEditor_Rotate_Flip(Menu):
    bl_label = "UV Editor, Rotate & Flip"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        op = context.window_manager.operator_properties_last("scale.xyz_2d")
        icon = 'PIVOT_CURSOR' if op.pivot_cursor else 'BLANK1'

        pie.separator()  # Left
        pie.operator("scale.xyz_2d", text="Flip Horizontal", icon=icon).x = -1   # Right
        pie.separator()  # Bottom
        pie.operator("scale.xyz_2d", text="Flip Vertical", icon=icon).y = -1     # Top

        pie.operator_context = 'EXEC_DEFAULT'
        pie.operator("transform.rotate", text="Rotate Counterclockwise (-90°)",  # Top_left
                     icon='BLANK1').value = radians(-90)
        pie.separator()  # Top_right

        pie.operator_context = 'INVOKE_DEFAULT'
        pie.operator("uv.align_edge_rotate_island", icon='BLANK1')               # Bottom_left

        pie.operator_context = 'EXEC_DEFAULT'
        pie.operator("transform.rotate", text="Rotate Clockwise (90°)",          # Bottom_right
                     icon='BLANK1').value = radians(90)


class MXD_MT_PIE_UVEditor_SnapToBoundary(Menu):
    bl_label = "UV Editor, Snap To Boundary"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("uv.snap_to_boundary", text="Left", icon='BLANK1').direction = "LEFT"
        pie.operator("uv.snap_to_boundary", text="Right", icon='BLANK1').direction = "RIGHT"
        pie.operator("uv.snap_to_boundary", text="Bottom", icon='BLANK1').direction = "BOTTOM"
        pie.operator("uv.snap_to_boundary", text="Top", icon='BLANK1').direction = "TOP"
        pie.operator("uv.snap_to_boundary", text="Top Left", icon='BLANK1').direction = "TOP_LEFT"
        pie.operator("uv.snap_to_boundary", text="Top Right", icon='BLANK1').direction = "TOP_RIGHT"
        pie.operator("uv.snap_to_boundary", text="Bottom Left", icon='BLANK1').direction = "BOTTOM_LEFT"
        pie.operator("uv.snap_to_boundary", text="Bottom Right", icon='BLANK1').direction = "BOTTOM_RIGHT"


class MXD_MT_PIE_UVEditor_AlignVerticesMoveIslands(Menu):
    bl_label = "UV Editor, Align Vertices, Move Islands"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("uv.align_vertices_move_islands", text="Left", icon='BLANK1').direction = "LEFT"
        pie.operator("uv.align_vertices_move_islands", text="Right", icon='BLANK1').direction = "RIGHT"
        pie.operator("uv.align_vertices_move_islands", text="Bottom", icon='BLANK1').direction = "BOTTOM"
        pie.operator("uv.align_vertices_move_islands", text="Top", icon='BLANK1').direction = "TOP"
        pie.operator("uv.get_distance", icon='BLANK1')  # Top Left
        pie.separator()  # Top Right
        pie.separator()  # Bottom Left
        pie.separator()  # Bottom Right



classes = (
    MXD_MT_PIE_UVEditor,
    MXD_MT_PIE_UVEditor_MarkEgde,
    MXD_MT_PIE_UVEditor_Rotate_Flip,
    MXD_MT_PIE_UVEditor_SnapToBoundary,
    MXD_MT_PIE_UVEditor_AlignVerticesMoveIslands,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
