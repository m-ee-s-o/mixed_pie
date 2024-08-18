from math import radians
import bpy
from bpy.types import Operator
from bpy.props import StringProperty


class MXD_OT_ShadeSmooth(Operator):
    bl_idname = "object.shade_auto_smooth_180"
    bl_label = "Shade Auto Smooth (180°)"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "180° Shade auto smooth."

    @classmethod
    def poll(cls, context):
        obj = context.object
        obj_type = (obj.type in {'MESH', 'CURVE', 'SURFACE'}) if obj else False
        if not obj:
            cls.poll_message_set("Object not found.")
        elif not obj_type:
            cls.poll_message_set("Object type must be Mesh, Curve, or Surface.")
        return obj and obj_type

    def invoke(self, context, event):
        from_edit = False
        if context.mode != 'OBJECT':
            from_edit = True
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.shade_auto_smooth(angle=radians(180))

        if from_edit:
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class MXD_OT_Edit_ToolSettings(Operator):
    bl_idname = "edit.tool_settings"
    bl_label = ""

    mode: StringProperty()

    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'PROPORTIONAL_EDITING':
                return "Toggle proportional editing.\n\n"  \
                       "Shift: Call tool panel"
            case 'AUTO_MERGE':
                return "Toggle auto merge.\n\n"            \
                       "Shift: Call options panel"

    def invoke(self, context, event):
        if not event.shift:
            tool_settings = context.scene.tool_settings
            match self.mode:
                case 'PROPORTIONAL_EDITING':
                    tool_settings.use_proportional_edit = not tool_settings.use_proportional_edit
                case 'AUTO_MERGE':
                    tool_settings.use_mesh_automerge = not tool_settings.use_mesh_automerge
        else:
            match self.mode:
                case 'PROPORTIONAL_EDITING':
                    bpy.ops.wm.call_panel(name="VIEW3D_PT_proportional_edit")
                case 'AUTO_MERGE':
                    bpy.ops.wm.call_panel(name="VIEW3D_PT_tools_meshedit_options")
        return {'FINISHED'}


class MXD_OT_UseSnap(Operator):
    bl_idname = "mode.use_snap"
    bl_label = "Snap"
    bl_description = "Toggle snap.\n\n"      \
                     "Shift: Call tool panel"

    def invoke(self, context, event):
        if not event.shift:
            tool_settings = context.scene.tool_settings
            tool_settings.use_snap = not tool_settings.use_snap
        else:
            bpy.ops.wm.call_panel(name="VIEW3D_PT_snapping")
        return {'FINISHED'}


classes = (
    MXD_OT_ShadeSmooth,
    MXD_OT_Edit_ToolSettings,
    MXD_OT_UseSnap,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
