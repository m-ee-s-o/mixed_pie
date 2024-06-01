import bpy
from bpy.types import Menu


class MXD_MT_PIE_Sculpt_BrushFalloff(Menu):
    bl_label = "Sculpt, Falloff"

    def draw(self, context):
        active = context.tool_settings.sculpt.brush.curve_preset

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("brush.falloff", text="Smoother" if (active == "SMOOTHER") else "Smooth",  # Left
                     icon='SMOOTHCURVE', depress=(active in {'SMOOTH', 'SMOOTHER'})
                     ).falloff = 'SMOOTH'
        pie.operator("brush.falloff", text="Sphere", icon='SPHERECURVE',                        # Right
                     depress=(active == 'SPHERE')).falloff = 'SPHERE'
        pie.operator("brush.falloff", text="Root", icon='ROOTCURVE',                            # Bottom
                     depress=(active == 'ROOT')).falloff = 'ROOT'
        pie.operator("brush.falloff", text="Inverse Square", icon='INVERSESQUARECURVE',         # Top
                     depress=(active == 'INVSQUARE')).falloff = 'INVSQUARE'
        pie.operator("brush.falloff", text="Sharper" if (active == "POW4") else "Sharp",        # Top_left
                     icon='SHARPCURVE', depress=(active in {'SHARP', 'POW4'})
                     ).falloff = 'SHARP'
        pie.operator("brush.falloff", text="Linear", icon='LINCURVE',                           # Top_right
                     depress=(active == 'LIN')).falloff = 'LIN'
        pie.operator("brush.falloff", text="Constant", icon='NOCURVE',                          # Bottom_left
                     depress=(active == 'CONSTANT')).falloff = 'CONSTANT'
        pie.operator("brush.falloff", text="Custom", icon='RNDCURVE',                           # Bottom_right
                     depress=(active == 'CUSTOM')).falloff = 'CUSTOM'


class MXD_MT_PIE_Sculpt_Brush(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        sculpt = context.tool_settings.sculpt
        falloff_shape = sculpt.brush.falloff_shape
        fs = "Falloff Shape: "
        use_accumulate = sculpt.brush.use_accumulate
        use_front_face = sculpt.brush.use_frontface
        lock_x = sculpt.lock_x
        lock_y = sculpt.lock_y
        lock_z = sculpt.lock_z

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.context_toggle", depress=(use_front_face), text="Front Faces Only",   # Left
                     icon='CHECKBOX_HLT' if use_front_face else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.sculpt.brush.use_frontface"

        pie.operator("wm.context_toggle", text="Lock X", depress=(lock_x),                     # Right
                     icon='CHECKBOX_HLT' if lock_x else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.sculpt.lock_x"

        pie.separator()  # Bottom

        op = pie.operator("wm.context_toggle_enum", icon='BLANK1',                             # Top
                          text=fs+("Sphere" if (falloff_shape == 'SPHERE') else "Projected"))
        op.data_path = "tool_settings.sculpt.brush.falloff_shape"
        op.value_1 = 'SPHERE'
        op.value_2 = 'PROJECTED'

        pie.operator("wm.context_toggle", depress=(use_accumulate), text="Accumulate",         # Top_left
                     icon='CHECKBOX_HLT' if use_accumulate else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.sculpt.brush.use_accumulate"

        pie.operator("wm.context_toggle", text="Lock Y", depress=(lock_y),                     # Top_right
                     icon='CHECKBOX_HLT' if lock_y else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.sculpt.lock_y"

        pie.separator()  # Bottom_left

        pie.operator("wm.context_toggle", text="Lock Z", depress=(lock_z),                     # Bottom_right
                     icon='CHECKBOX_HLT' if lock_z else 'CHECKBOX_DEHLT'
                     ).data_path = "tool_settings.sculpt.lock_z"


classes = (
    MXD_MT_PIE_Sculpt_BrushFalloff,
    MXD_MT_PIE_Sculpt_Brush,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
