import bpy
from bpy.types import Operator


class MXD_OT_UV_UseSnap(Operator):
    bl_idname = "uv.use_snap"
    bl_label = "Snap"
    bl_description = "Toggle snap.\n\n"        \
                     "Shift: Call tool panel"

    def invoke(self, context, event):
        if not event.shift:
            tool_settings = context.scene.tool_settings
            tool_settings.use_snap_uv = not tool_settings.use_snap_uv
        else:
            bpy.ops.wm.call_panel(name="IMAGE_PT_snapping")
        return {'FINISHED'}


classes = (
    MXD_OT_UV_UseSnap,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
