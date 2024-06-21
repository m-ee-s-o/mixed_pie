import bpy
from bpy.types import Panel
from .scripts_init import script_categories


class MXD_PT_Scripts(Panel):
    bl_label = "Scripts"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 15
        col = layout.box().column()

        for category, scripts in script_categories.items():
            col.label(text=category)
            for index, script in enumerate(scripts):
                row = col.row(align=True)
                row.label(text=script.name)
                row.separator()

                appendable = getattr(script, "pie_appendable_script", False)
                if appendable:
                    op = row.operator("script.execute", text="", icon='TRIA_RIGHT' if not appendable else 'ADD')
                    op.category = category
                    op.index = index
                    op.tooltip = script.tooltip
                    op.append_to_pie_as = script.name[script.name.index("- ") + 1:]
                    row.separator(factor=0.4)

                op = row.operator("script.execute", text="", icon='TRIA_RIGHT')
                op.category = category
                op.index = index
                op.tooltip = script.tooltip                


classes = (
    MXD_PT_Scripts,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
