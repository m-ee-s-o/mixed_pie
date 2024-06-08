import bpy
from bpy.types import Menu


class MXD_MT_PIE_PaintWeight_BrushFalloff(Menu):
    bl_label = "Paint: Weight, Falloff"

    def draw(self, context):
        active = context.tool_settings.weight_paint.brush.curve_preset

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("brush.falloff", text="Smoother" if (active == "SMOOTHER") else "Smooth",  # Left
                     depress=(active in {'SMOOTH', 'SMOOTHER'}),
                     icon='SMOOTHCURVE').falloff = 'SMOOTH'
        pie.operator("brush.falloff", text="Sphere", icon='SPHERECURVE',                        # Right
                     depress=(active == 'SPHERE')).falloff = 'SPHERE'
        pie.operator("brush.falloff", text="Root", icon='ROOTCURVE',                            # Bottom
                     depress=(active == 'ROOT')).falloff = 'ROOT'
        pie.operator("brush.falloff", text="Inverse Square", icon='INVERSESQUARECURVE',         # Top
                     depress=(active == 'INVSQUARE')).falloff = 'INVSQUARE'
        pie.operator("brush.falloff", text="Sharper" if (active == "POW4") else "Sharp",        # Top_left
                     depress=(active in {'SHARP', 'POW4'}),
                     icon='SHARPCURVE').falloff = 'SHARP'
        pie.operator("brush.falloff", text="Linear", icon='LINCURVE',                           # Top_right
                     depress=(active == 'LIN')).falloff = 'LIN'
        pie.operator("brush.falloff", text="Constant", icon='NOCURVE',                          # Bottom_left
                     depress=(active == 'CONSTANT')).falloff = 'CONSTANT'
        pie.operator("brush.falloff", text="Custom", icon='RNDCURVE',                           # Bottom_right
                     depress=(active == 'CUSTOM')).falloff = 'CUSTOM'


class MXD_MT_PIE_PaintWeight_Toolbar(Menu):
    bl_label = "Paint: Weight, Toolbar"

    def draw(self, context):
        active = context.workspace.tools.from_space_view3d_mode(context.mode).idname

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin_brush.Blur'),     # Left
                     text="Blur",).name = 'builtin_brush.Blur'
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin.sample_weight'),  # Right
                     text="Sample Weight").name = 'builtin.sample_weight'
        pie.separator()  # Bottom
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin_brush.Average'),  # Top
                     text="Average").name = 'builtin_brush.Average'
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin_brush.Smear'),    # Top_left
                     text="Smear").name = 'builtin_brush.Smear'
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin.gradient'),       # Top_right
                     text="Gradient").name = 'builtin.gradient'
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin_brush.Draw'),     # Bottom_left
                     text="Draw").name = 'builtin_brush.Draw'
        pie.operator("wm.tool_set_by_id", depress=(active == 'builtin.annotate'),       # Bottom_right
                     text="Annotate").name = 'builtin.annotate'


class MXD_MT_PIE_PaintWeight_Brush(Menu):
    bl_label = "Paint: Weight"

    def draw(self, context):
        tool_settings = context.tool_settings

        data_path_weight = ("tool_settings.unified_paint_settings.weight"
                     if tool_settings.unified_paint_settings.use_unified_weight else
                     "tool_settings.weight_paint.brush.weight")
        weight_value = eval("context." + data_path_weight)

        brush = tool_settings.weight_paint.brush
        falloff_shape = tool_settings.weight_paint.brush.falloff_shape
        fs = "Falloff Shape: "
        use_accumulate = brush.use_accumulate
        use_front_face = brush.use_frontface
        paint_through = context.scene.paint_through.weight

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.context_toggle", depress=(use_front_face), text="Front Faces Only",                                     # Left
                     icon='CHECKBOX_HLT' if use_front_face else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.weight_paint.brush.use_frontface"

        pie.separator()                                                                                                          # Right

        pie.operator("wm.call_menu_pie", text="Armature", icon='ARMATURE_DATA').name = "MXD_MT_PIE_Armature"                     # Bottom

        op = pie.operator("wm.context_toggle_enum", icon='BLANK1',                                                               # Top
                          text=fs+("Sphere" if (falloff_shape == 'SPHERE') else "Projected"))
        op.data_path = "tool_settings.weight_paint.brush.falloff_shape"
        op.value_1 = 'SPHERE'
        op.value_2 = 'PROJECTED'

        pie.operator("wm.context_toggle", depress=(use_accumulate), text="Accumulate",                                           # Top_left
                     icon='CHECKBOX_HLT' if use_accumulate else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.weight_paint.brush.use_accumulate"

        op = pie.operator("wm.context_set_float", text=f"Weight: {weight_value:n}", depress=(weight_value == 1), icon='BLANK1')  # Top_right
        op.data_path = data_path_weight
        op.value = 1 - weight_value

        pie.operator("wm.context_toggle", depress=(paint_through),                                                               # Bottom_left
                     icon='CHECKBOX_HLT' if paint_through else 'CHECKBOX_DEHLT',
                     text="Paint Through").data_path = "scene.paint_through.weight"

        pie.separator()                                                                                                          # Bottom_right


classes = (
    MXD_MT_PIE_PaintWeight_BrushFalloff,
    MXD_MT_PIE_PaintWeight_Toolbar,
    MXD_MT_PIE_PaintWeight_Brush,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
