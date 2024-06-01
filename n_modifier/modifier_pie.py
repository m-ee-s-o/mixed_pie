import bpy
from bpy.types import Menu


class MXD_MT_PIE_Modifier(Menu):
    bl_label = "Modifier"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("modifier.add", text="_Subdivision Surface",                                    # Left
                     icon='MOD_SUBSURF').modifier = "subdivision surface"
        pie.separator()  # Right
        pie.operator("modifier.add_data_transfer", text="_Data Transfer", icon='MOD_DATA_TRANSFER')   # Bottom
        pie.separator()  # Top
        pie.operator("modifier.add", text="_Mirror", icon='MOD_MIRROR').modifier = "mirror"          # Top_left
        pie.separator()  # Top_right
        pie.operator("modifier.add", text="_Solidify (IH)",                                          # Bottom_left
                     icon='MOD_SOLIDIFY').modifier = "solidify (for inverted hull)"
        pie.separator()  # Bottom_right


class MXD_MT_PIE_Modifier_Symmetrize(Menu):
    bl_label = "Symmetrize"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("modifier.symmetrize", text="-X", icon='BLANK1') # Left
        op.axis = (True, False, False)
        op.bisect = (True, False, False)

        op = pie.operator("modifier.symmetrize", text="+X", icon='BLANK1')  # Right
        op.axis = (True, False, False)
        op.bisect = (True, False, False)
        op.flip = (True, False, False)

        pie.separator()  # Bottom
        pie.separator()  # Top

        op = pie.operator("modifier.symmetrize", text="+Y", icon='BLANK1')          # Top_left
        op.axis = (False, True, False)
        op.bisect = (False, True, False)
        op.flip = (False, True, False)

        op = pie.operator("modifier.symmetrize", text="+Z", icon='BLANK1')          # Top_right
        op.axis = (False, False, True)
        op.bisect = (False, False, True)
        op.flip = (False, False, True)

        op = pie.operator("modifier.symmetrize", text="-Y", icon='BLANK1')          # Bottom_left
        op.axis = (False, True, False)
        op.bisect = (False, True, False)

        op = pie.operator("modifier.symmetrize", text="-Z", icon='BLANK1')          # Bottom_right
        op.axis = (False, False, True)
        op.bisect = (False, False, True)


classes = (
    MXD_MT_PIE_Modifier,
    MXD_MT_PIE_Modifier_Symmetrize,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
