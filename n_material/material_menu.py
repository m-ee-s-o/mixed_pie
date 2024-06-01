import bpy
from bpy.types import Menu


class MXD_MT_Menu_Material_Preset(Menu):
    bl_label = "Material Preset"

    @classmethod
    def poll(self, context):
        area = context.area
        if area.ui_type == 'PROPERTIES':
            return (area.spaces[0].context == 'MATERIAL')
        return False

    def draw(self, context):
        layout = self.layout
        layout.operator("material.preset", text="Image Layers").type = 'IMAGE_LAYERS'
        layout.operator("material.preset", text="Outline").type = 'OUTLINE'
        layout.separator()
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("material.preset", text="Emission").type = 'EMISSION'


classes = (
    MXD_MT_Menu_Material_Preset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
