import bpy
from bpy.types import Menu


class MXD_MT_PIE_Node(Menu):
    bl_label = "Node"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left

        op = pie.operator("node.add", text="Multiply RGBA", icon='BLANK1')         # Right
        op.type = 'ShaderNodeMix'
        op.settings.add().set("data_type", "'RGBA'")
        op.settings.add().set("blend_type", "'MULTIPLY'")

        pie.separator()  # Bottom
        pie.separator()  # Top
        pie.separator()  # Top_left

        op = pie.operator("node.add", text="Mix RGBA", icon='BLANK1')              # Top_right
        op.type = 'ShaderNodeMix'
        op.settings.add().set("data_type", "'RGBA'")

        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_Node,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
