import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


class MXD_OT_Object_ClearTransform(Operator):
    bl_idname = "object.clear_transform"
    bl_label = "Clear Tranform"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear unapplied transform"

    location: BoolProperty(name="Clear Location")
    rotation: BoolProperty(name="Clear Rotation")
    scale: BoolProperty(name="Clear Scale")

    @classmethod
    def poll(cls, context):
        if not (obj := context.object):
            cls.poll_message_set("Object not found.")
        return (context.mode == 'OBJECT') and obj

    def execute(self, context):
        if self.location:
            bpy.ops.object.location_clear()
        if self.rotation:
            bpy.ops.object.rotation_clear()
        if self.scale:
            bpy.ops.object.scale_clear()
        return {'FINISHED'}


class MXD_OT_Object_ProportionalEditing(Operator):
    bl_idname = "object.use_proportional_editing"
    bl_label = "Proportional Editing"
    bl_description = "Toggle proportional editing.\n\n"  \
                     "Shift: Call tool panel"

    def invoke(self, context, event):
        if not event.shift:
            tool_settings = context.scene.tool_settings
            tool_settings.use_proportional_edit_objects = not tool_settings.use_proportional_edit_objects
        else:
            bpy.ops.wm.call_panel(name="VIEW3D_PT_proportional_edit")
        return {'FINISHED'}


classes = (
    MXD_OT_Object_ClearTransform,
    MXD_OT_Object_ProportionalEditing,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
