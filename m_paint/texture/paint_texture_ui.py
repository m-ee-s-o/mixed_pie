import bpy
from bpy.types import Menu#, IMAGE_HT_header


class MXD_MT_PIE_PaintTexture_BrushFalloff(Menu):
    bl_label = "Paint: Texture, Falloff"

    def draw(self, context):
        active = context.tool_settings.image_paint.brush.curve_preset

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("brush.falloff", text="Smoother" if (active == "SMOOTHER") else "Smooth",  # Left
                     depress=(active in {'SMOOTH', 'SMOOTHER'}),
                     icon='SMOOTHCURVE').falloff = 'SMOOTH'
        pie.operator("brush.falloff", text="Sphere", depress=(active == 'SPHERE'),              # Right
                     icon='SPHERECURVE').falloff = 'SPHERE'
        pie.operator("brush.falloff", text="Root", depress=(active == 'ROOT'),                  # Bottom
                     icon='ROOTCURVE').falloff = 'ROOT'
        pie.operator("brush.falloff", text="Inverse Square", depress=(active == 'INVSQUARE'),   # Top
                     icon='INVERSESQUARECURVE').falloff = 'INVSQUARE'
        pie.operator("brush.falloff", text="Sharper" if (active == "POW4") else "Sharp",        # Top_left
                     depress=(active in {'SHARP', 'POW4'}),
                     icon='SHARPCURVE').falloff = 'SHARP'
        pie.operator("brush.falloff", text="Linear", depress=(active == 'LIN'),                 # Top_right
                     icon='LINCURVE').falloff = 'LIN'
        pie.operator("brush.falloff", text="Constant", depress=(active == 'CONSTANT'),          # Bottom_left
                     icon='NOCURVE').falloff = 'CONSTANT'
        pie.operator("brush.falloff", text="Custom", depress=(active == 'CUSTOM'),              # Bottom_right
                     icon='RNDCURVE').falloff = 'CUSTOM'


class MXD_MT_PIE_PaintTexture_Toolbar(Menu):
    bl_label = "Paint: Texture, Toolbar"

    @classmethod
    def poll(self, context):
        area = context.area
        if area.ui_type == 'IMAGE_EDITOR':
            if area.spaces.active.ui_mode != 'PAINT':
                return False
        return (context.mode in {'PAINT_TEXTURE', 'PAINT_WEIGHT', 'SCULPT'})

    def draw(self, context):
        active = context.workspace.tools.from_space_view3d_mode(context.mode).idname

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Soften"),  # Left
                     text="Soften").name = "builtin_brush.Soften"
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Mask"),    # Right
                     text="Mask").name = "builtin_brush.Mask"
        pie.separator()  # Bottom
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Clone"),   # Top
                     text="Clone").name = "builtin_brush.Clone"
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Smear"),   # Top_left
                     text="Smear").name = "builtin_brush.Smear"
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Fill"),    # Top_right
                     text="Fill").name = "builtin_brush.Fill"
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin_brush.Draw"),    # Bottom_left
                     text="Draw").name = "builtin_brush.Draw"
        pie.operator("wm.tool_set_by_id", depress=(active == "builtin.annotate"),      # Bottom_right
                     text="Annotate").name = "builtin.annotate"


class MXD_MT_PIE_PaintTexture(Menu):
    bl_label = "Paint: Texture"

    def draw(self, context):
        affect_alpha = context.tool_settings.image_paint.brush.use_alpha
        paint_through = context.scene.paint_through.texture
        blend_mode_path = "tool_settings.image_paint.brush.blend"
        active = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        has_blend_mode = (active in {"builtin_brush.Draw", "builtin_brush.Fill"})
        view_3d = (context.area.ui_type == 'VIEW_3D')

        layout = self.layout
        pie = layout.menu_pie()

        if view_3d:
            pie.operator("wm.context_toggle", depress=(affect_alpha),
                         icon='CHECKBOX_HLT' if affect_alpha else 'CHECKBOX_DEHLT',
                         text="Affect Alpha").data_path = "tool_settings.image_paint.brush.use_alpha"
        else:
            pie.separator()   # Left

        pie.separator()  # Right
        pie.separator()  # Bottom

        if has_blend_mode:
            op = pie.operator("wm.context_toggle_enum", text="Mix | RemoveAlpha", icon='BLANK1')
            op.data_path = blend_mode_path
            op.value_1 = 'ERASE_ALPHA'
            op.value_2 = 'MIX'
        else:
            pie.separator()  # Top

        pie.operator("wm.call_panel", text="Image Layers",                                            # Top_left
                     icon='IMAGE_DATA').name = "MXD_PT_PaintTexture_ImageLayersPanel"

        pie.separator()  # Top_right

        if view_3d:
            pie.operator("wm.context_toggle", depress=(paint_through),
                         icon='CHECKBOX_HLT' if paint_through else 'CHECKBOX_DEHLT',
                         text="Paint Through").data_path = "scene.paint_through.texture"
        else:
            pie.separator()  # Bottom_left

        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_PaintTexture_BrushFalloff,
    MXD_MT_PIE_PaintTexture_Toolbar,
    MXD_MT_PIE_PaintTexture,
)


# def reload_image(self, context):
#     self.layout.operator("image.reload")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # IMAGE_HT_header.append(reload_image)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # IMAGE_HT_header.remove(reload_image)
