import bpy
from bpy.types import Menu


class MXD_MT_PIE_EditCurve(Menu):
    bl_label = "Edit: Curve"

    def draw(self, context):
        tool_settings = context.scene.tool_settings
        snap = tool_settings.use_snap
        proportional_editing = tool_settings.use_proportional_edit
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left
        pie.separator()  # Right
        pie.separator()  # Bottom
        pie.operator("mode.use_snap", depress=(snap),                                    # Top
                     icon='CHECKBOX_HLT' if snap else 'CHECKBOX_DEHLT')
        pie.separator()  # Top_left
        pie.operator("edit.tool_settings", depress=(proportional_editing),               # Top_right
                     icon='CHECKBOX_HLT' if proportional_editing else 'CHECKBOX_DEHLT',
                     text="Proportional Editing").mode = 'PROPORTIONAL_EDITING'
        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_EditCurve,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
