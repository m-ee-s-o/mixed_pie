import bpy
from bpy.types import Menu


class MXD_MT_PIE_Scale_VP(Menu):
    bl_label = "Scale, 3D View"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("scale.xyz_3d", text="Scale X by 0", icon='PIVOT_CURSOR')   # Left
        op.x = 0
        op.pivot_cursor = True

        pie.operator("scale.xyz_3d", text="Scale X by 0", icon='BLANK1').x = 0        # Right
        pie.operator("scale.xyz_3d", text="Scale X by -1", icon='BLANK1').x = -1      # Bottom

        op = pie.operator("scale.xyz_3d", text="Scale X by -1", icon='PIVOT_CURSOR')  # Top
        op.x = -1
        op.pivot_cursor = True

        op = pie.operator("scale.xyz_3d", text="Scale Y by 0", icon='PIVOT_CURSOR')   # Top_left
        op.y = 0
        op.pivot_cursor = True

        pie.operator("scale.xyz_3d", text="Scale Y by 0", icon='BLANK1').y = 0        # Top_right

        op = pie.operator("scale.xyz_3d", text="Scale Z by 0", icon='PIVOT_CURSOR')   # Bottom_left
        op.z = 0
        op.pivot_cursor = True

        pie.operator("scale.xyz_3d", text="Scale Z by 0", icon='BLANK1').z = 0        # Bottom_right


class MXD_MT_PIE_Scale_UVE(Menu):
    bl_label = "Scale, UV Editor"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        op = context.window_manager.operator_properties_last("scale.xyz_2d")
        icon = 'PIVOT_CURSOR' if op.pivot_cursor else 'BLANK1'

        pie.operator("scale.xyz_2d", text="Scale X by 0", icon=icon).x = 0       # Left
        pie.operator("scale.xyz_2d", text="Scale X by 0", icon=icon).x = 0       # Right
        pie.operator("scale.xyz_2d", text="Scale Y by 0", icon=icon).y = 0       # Bottom
        pie.operator("scale.xyz_2d", text="Scale Y by 0", icon=icon).y = 0       # Top
        pie.operator("uv.scale_cage", icon='ORIENTATION_GLOBAL')                 # Top_left
        pie.operator("uv.snap_cursor", icon='PIVOT_CURSOR').target = 'SELECTED'  # Top_right
        pie.operator("uv.average_islands_scale", icon='BLANK1')                  # Bottom_left
        pie.operator("uv.equalize_scale_xy", icon='BLANK1')                      # Bottom_right


class MXD_MT_PIE_Scale_NE(Menu):
    bl_label = "Scale, Node Editor"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("scale.xyz_2d", text="Scale X by 0", icon='BLANK1').x = 0  # Left
        pie.separator()  # Right
        pie.separator()  # Bottom
        pie.operator("scale.xyz_2d", text="Scale Y by 0", icon='BLANK1').y = 0  # Top
        pie.separator()  # Top_left
        pie.separator()  # Top_right
        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_Scale_VP,
    MXD_MT_PIE_Scale_UVE,
    MXD_MT_PIE_Scale_NE,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
