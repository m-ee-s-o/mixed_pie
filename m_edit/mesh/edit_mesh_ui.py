import bpy
from bpy.types import Menu, Panel
import addon_utils
from ...f_scripts.scripts_utils import ScriptAppendablePie


class MXD_MT_PIE_EditMesh(Menu, ScriptAppendablePie):
    bl_label = "Edit: Mesh"

    def draw(self, context):
        layout = self.layout
        tool_settings = context.scene.tool_settings
        snap = tool_settings.use_snap
        auto_merge = tool_settings.use_mesh_automerge
        proportional_editing = tool_settings.use_proportional_edit

        pie = self.pie_wrapper(layout.menu_pie())
        pie.right("edit.tool_settings", depress=(auto_merge), icon='CHECKBOX_HLT' if auto_merge else 'CHECKBOX_DEHLT', text="Auto Merge").mode = 'AUTO_MERGE'
        pie.top("mode.use_snap", depress=(snap), icon='CHECKBOX_HLT' if snap else 'CHECKBOX_DEHLT')
        pie.top_right("edit.tool_settings", depress=(proportional_editing), icon='CHECKBOX_HLT' if proportional_editing else 'CHECKBOX_DEHLT', text="Proportional Editing").mode = 'PROPORTIONAL_EDITING'
        pie.bottom_right("mesh.remove_doubles", icon='BLANK1').threshold = 0.000001
        pie.draw()


class MXD_MT_PIE_EditMesh_MarkEgde(Menu):
    bl_label = "Edit: Mesh, Mark Edge"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator_context = 'EXEC_DEFAULT'  # Only calls op.execute, skipping any modal

        pie.operator("mesh.mark_seam", text="Clear Seam", icon='BLANK1').clear = True           # Left
        pie.operator("mesh.mark_seam", icon='BLANK1')                                           # Right
        pie.separator()  # Bottom
        pie.separator()  # Top
        pie.operator("transform.edge_crease", text="Clear Crease", icon='BLANK1').value = -1.0  # Top_left
        pie.operator("transform.edge_crease", icon='BLANK1').value = 1.0                        # Top_right
        pie.operator("mesh.mark_sharp", text="Clear Sharp", icon='BLANK1').clear = True         # Bottom_left
        pie.operator("mesh.mark_sharp", icon='BLANK1')                                          # Bottom_right


# SELECT---------------------------------------------------------------------------------------------------


class MXD_MT_PIE_EditMesh_Select(Menu):
    bl_label = "Edit: Mesh, Select"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("mesh.select_nth", icon='BLANK1')                                       # Left
        pie.operator("wm.call_menu_pie", text="Select Loops",                                # Right
                     icon='ADD').name = "MXD_MT_PIE_SelectLoops"
        pie.separator()  # Bottom
        pie.operator("wm.call_menu_pie", text="Select All by Trait",                         # Top
                     icon='ADD').name = "MXD_MT_PIE_SelectAllByTrait"
        pie.operator("mesh.edges_select_sharp", icon='BLANK1')                               # Top_left
        pie.operator("wm.call_panel", text="Select More/Less",                               # Top_right
                     icon='ADD').name = "MXD_PT_SelectMoreOrLess"
        pie.operator("mesh.select_random", icon='BLANK1')                                    # Bottom_left
        pie.operator("mesh.select_axis", text="Side of Active", icon='BLANK1').sign = 'NEG'  # Bottom_right


class MXD_MT_PIE_SelectAllByTrait(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left
        pie.separator()  # Right
        pie.separator()  # Bottom
        pie.separator()  # Top
        pie.operator("mesh.select_loose", icon='BLANK1')           # Top_left
        pie.operator("mesh.select_interior_faces", icon='BLANK1')  # Top_right
        pie.operator("mesh.select_non_manifold", icon='BLANK1')    # Bottom_left
        pie.operator("mesh.select_face_by_sides", icon='BLANK1')   # Bottom_right


class MXD_MT_PIE_SelectLoops(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left
        pie.separator()  # Right
        pie.separator()  # Bottom
        pie.separator()  # Top
        pie.operator("mesh.loop_multi_select", text="Edge Rings", icon='BLANK1').ring = True   # Top_left
        pie.operator("mesh.loop_to_region", icon='BLANK1')                                     # Top_right
        pie.operator("mesh.loop_multi_select", text="Edge Loops", icon='BLANK1').ring = False  # Bottom_left
        pie.operator("mesh.region_to_loop", icon='BLANK1')                                     # Bottom_right


class MXD_PT_SelectMoreOrLess(Panel):
    bl_label = ""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.label()
        col = layout.column()
        split = col.split(align=True)
        split.operator("mesh.select_less")
        split.operator("mesh.select_more")
        col = layout.column(align=True)
        col.operator("mesh.select_next_item")
        col.operator("mesh.select_prev_item")


# ---------------------------------------------------------------------------------------------------------


class MXD_MT_PIE_LoopTools(Menu):
    bl_label = "Edit: Mesh, LoopTools"

    @classmethod
    def poll(self, context):
        # https://blender.stackexchange.com/questions/43703/how-to-tell-if-an-add-on-is-present-using-python
        return addon_utils.check("bl_ext.blender_org.looptools") == (True, True)

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("mesh.looptools_circle", icon='BLANK1')                              # Left
        pie.operator("mesh.looptools_bridge", text="Loft", icon='BLANK1').loft = True     # Right
        pie.operator("mesh.looptools_space", icon='BLANK1')                               # Bottom
        pie.operator("mesh.looptools_flatten", icon='BLANK1')                             # Top
        pie.operator("mesh.looptools_curve", icon='BLANK1')                               # Top_left
        pie.operator("mesh.looptools_gstretch", icon='BLANK1')                            # Top_right
        pie.operator("mesh.looptools_bridge", text="Bridge", icon='BLANK1').loft = False  # Bottom_left
        pie.operator("mesh.looptools_relax", icon='BLANK1')                               # Bottom_right


classes = (
    MXD_MT_PIE_EditMesh,
    MXD_MT_PIE_EditMesh_MarkEgde,
    MXD_MT_PIE_EditMesh_Select,
    MXD_MT_PIE_SelectAllByTrait,
    MXD_MT_PIE_SelectLoops,
    MXD_PT_SelectMoreOrLess,
    MXD_MT_PIE_LoopTools,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
