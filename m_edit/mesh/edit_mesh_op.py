from math import radians
import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty


class MXD_OT_ShadeSmooth(Operator):
    bl_idname = "shade.smooth"
    bl_label = "Shade Smooth"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "180° Shade auto smooth.\n\n"     \
                     "Ctrl: 30° Shade auto smooth.\n"  \
                     "Shift: Shade flat"

    mode: StringProperty(options={'HIDDEN'})
    option: EnumProperty(items=[('180°', "Shade Auto Smooth (180°)", ""),
                                ('30°', "Shade Auto Smooth (30°)", ""),
                                ('0°', "Shade Flat", "")],
                         name="")

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
        if not (event.ctrl or event.shift):
            self.option = '180°'
        elif event.ctrl:
            self.option = '30°'
        elif event.shift:
            self.option = '0°'
        return self.execute(context)

    def execute(self, context):
        if self.mode == 'NON_OBJ':
            bpy.ops.object.mode_set(mode='OBJECT')
        match self.option:
            case '180°':
                bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=radians(180))
            case '30°':
                bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=radians(30))
            case '0°':
                bpy.ops.object.shade_flat()
        if self.mode == 'NON_OBJ':
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
