import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty
from .scripts_init import scripts


class MXD_OT_Scripts_Execute(Operator):
    bl_idname = "scripts.execute"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = ""

    category: StringProperty(options={'HIDDEN'})
    index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        scripts[self.category][self.index](context)

        return {'FINISHED'}


classes = (
    MXD_OT_Scripts_Execute,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
