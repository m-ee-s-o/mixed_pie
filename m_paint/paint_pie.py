import bpy
from bpy.types import Menu


class MXD_MT_PIE_BrushStrokeMethod(Menu):
    bl_label = "Paint: Stroke Method"

    @classmethod
    def poll(self, context):
        return (context.mode in {'PAINT_TEXTURE', 'PAINT_WEIGHT', 'SCULPT'})

    def draw(self, context):
        not_paint_weight = (context.mode != 'PAINT_WEIGHT')
        tool_settings = context.tool_settings
        mode = context.mode
        match mode:
            case 'PAINT_WEIGHT':
                active = tool_settings.weight_paint.brush.stroke_method
                data_path = "tool_settings.weight_paint.brush.stroke_method"
            case 'SCULPT':
                active = tool_settings.sculpt.brush.stroke_method
                data_path = "tool_settings.sculpt.brush.stroke_method"
            case _:
                if (mode == 'PAINT_TEXTURE') or (context.area.ui_type == 'IMAGE_EDITOR'):
                    active = tool_settings.image_paint.brush.stroke_method
                    data_path = "tool_settings.image_paint.brush.stroke_method"

        layout = self.layout
        pie = layout.menu_pie()

        if not_paint_weight:
            op = pie.operator("wm.context_set_enum", depress=(active == 'DRAG_DOT'), text="Drag Dot", icon='BLANK1')
            op.data_path = data_path
            op.value = 'DRAG_DOT'
        else:
            pie.separator()  # Left

        op = pie.operator("wm.context_set_enum", depress=(active == 'LINE'), text="Line", icon='BLANK1')          # Right
        op.data_path = data_path
        op.value = 'LINE'

        op = pie.separator()  # Bottom

        op = pie.operator("wm.context_set_enum", depress=(active == 'AIRBRUSH'), text="Airbrush", icon='BLANK1')  # Top
        op.data_path = data_path
        op.value = 'AIRBRUSH'

        op = pie.operator("wm.context_set_enum", depress=(active == 'SPACE'), text="Space", icon='BLANK1')        # Top_left
        op.data_path = data_path
        op.value = 'SPACE'

        if not_paint_weight:
            op = pie.operator("wm.context_set_enum", depress=(active == 'ANCHORED'), text="Anchored", icon='BLANK1')
            op.data_path = data_path
            op.value = 'ANCHORED'
        else:
            pie.separator()  # Top_right

        op = pie.operator("wm.context_set_enum", depress=(active == 'DOTS'), text="Dots", icon='BLANK1')          # Bottom_left
        op.data_path = data_path
        op.value = 'DOTS'

        op = pie.operator("wm.context_set_enum", depress=(active == 'CURVE'), text="Curve", icon='BLANK1')        # Bottom_right
        op.data_path = data_path
        op.value = 'CURVE'


classes = (
    MXD_MT_PIE_BrushStrokeMethod,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
