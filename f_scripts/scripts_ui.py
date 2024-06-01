import bpy
from bpy.types import Panel
from .scripts_init import scripts


class MXD_PT_Scripts(Panel):
    bl_label = "Scripts"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        col = layout.box().column()

        for category, functions in scripts.items():
            col.label(text=category)
            for index, func in enumerate(functions):
                row = col.row()
                row.label(text=f"    - {func.__name__.replace('_', ' ')}")
                op = row.operator("scripts.execute", text="", icon='TRIA_RIGHT')
                op.category = category
                op.index = index


classes = (
    MXD_PT_Scripts,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
