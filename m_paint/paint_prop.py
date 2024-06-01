import bpy
from bpy.types import PropertyGroup, Scene
from bpy.props import BoolProperty, PointerProperty


class PaintThrough(PropertyGroup):
    def get_texture(self):
        image_paint = bpy.context.scene.tool_settings.image_paint
        return not (image_paint.use_occlude or image_paint.use_backface_culling)

    def set_texture(self, value):
        image_paint = bpy.context.scene.tool_settings.image_paint
        if value:
            self['texture_use_occlude'] = image_paint.use_occlude
            self['texture_use_backface_culling'] = image_paint.use_backface_culling
            image_paint.use_occlude = False
            image_paint.use_backface_culling = False         
        else:
            image_paint.use_occlude = self.get("texture_use_occlude", True)
            image_paint.use_backface_culling = self.get("texture_use_backface_culling", True)

    def get_weight(self):
        brush = bpy.context.tool_settings.weight_paint.brush
        return (not brush.use_frontface) and (brush.falloff_shape == 'PROJECTED')

    def set_weight(self, value):
        brush = bpy.context.tool_settings.weight_paint.brush
        if value:
            self['weight_use_frontface'] = brush.use_frontface
            self['weight_falloff_shape'] = brush.falloff_shape
            brush.use_frontface = False
            brush.falloff_shape = 'PROJECTED'       
        else:
            brush.use_frontface = self.get("weight_use_frontface", True)
            brush.falloff_shape = self.get("weight_falloff_shape", 'SPHERE')

    texture: BoolProperty(get=get_texture, set=set_texture)
    weight: BoolProperty(get=get_weight, set=set_weight)


classes = (
    PaintThrough,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Scene.paint_through = PointerProperty(type=PaintThrough)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Scene.paint_through
