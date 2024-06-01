import bpy
from bpy.types import Operator
from bpy.props import StringProperty


class MXD_OT_BrushFalloff(Operator):
    bl_idname = "brush.falloff"
    bl_label = "Brush Falloff"

    falloff: StringProperty()

    @classmethod
    def poll(cls, context):
        return (context.mode in {'PAINT_TEXTURE', 'PAINT_WEIGHT', 'SCULPT'})

    @classmethod
    def description(cls, context, properties):
        description = "Change brush falloff"
        match properties.falloff:
            case 'SMOOTH':
                description += ".\n\nShift: [Smoother] falloff"
            case 'SHARP':
                description += ".\n\nShift: [Sharper] falloff"
            case 'CUSTOM':
                description += ".\n\nShift: Call falloff panel"
        return description

    def invoke(self, context, event):
        match context.mode:
            case 'PAINT_TEXTURE':
                brush = context.tool_settings.image_paint.brush
            case 'PAINT_WEIGHT':
                brush = context.tool_settings.weight_paint.brush
            case 'SCULPT':
                brush = context.tool_settings.sculpt.brush
        if event.shift:
            match self.falloff:
                case 'SMOOTH':
                    self.falloff = 'SMOOTHER'
                    brush.curve_preset = self.falloff
                    self.report({'INFO'}, "Smoother")
                case 'SHARP':
                    self.falloff = 'POW4'
                    brush.curve_preset = self.falloff
                    self.report({'INFO'}, "Sharper")
                case 'CUSTOM':
                    brush.curve_preset = self.falloff
                    bpy.ops.wm.call_panel(name="VIEW3D_PT_tools_brush_falloff")
                case _:  # If somehow shift was clicked for others
                    brush.curve_preset = self.falloff
        else:
            match self.falloff:
                case 'SMOOTH':
                    brush.curve_preset = self.falloff
                case 'SHARP':
                    brush.curve_preset = self.falloff
                case 'CUSTOM':
                    brush.curve_preset = self.falloff
                case _:
                    brush.curve_preset = self.falloff
        return {'FINISHED'}


classes = (
    MXD_OT_BrushFalloff,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
