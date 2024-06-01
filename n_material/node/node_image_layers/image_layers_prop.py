import bpy
from bpy.types import Material, PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.app.handlers import persistent, save_pre
from .bake_preview import BakePreview


_node_groups = []
_image_layers_panel_dock_mode = []


def callback_target_node_group(self, context):
    target = self.get("_target_node_group", "—")
    nodes = context.object.active_material.node_tree.nodes
    node = nodes.get(target)
    item = (node.name, self.name_format(node), "") if node else ('—', "—", "")
    _node_groups.clear()
    _node_groups.append(item)
    for node in nodes:
        if (node.bl_idname == 'ShaderNodeGroup'
                and node.name != target
                and (node_tree := node.node_tree)
                and node_tree.nodes.get(f"DoNotChange_PropertyStorage")):
            _node_groups.append((node.name, self.name_format(node, sub=True), ""))
    return _node_groups


class Material_ImageLayers(BakePreview, PropertyGroup):
    def name_format(self, node, sub=False):
        return f"{'        ' if sub else ''}{node.name} [{node.node_tree.name}]"

    def set_target_node_group(self, value):
        self['_target_node_group'] = _node_groups[value][0]

    target_node_group: EnumProperty(name="Target Group Node [Node Tree]", items=callback_target_node_group,
                                    set=set_target_node_group)
    
    is_preview_shown: BoolProperty(name="Preview with Alpha", get=BakePreview.get_bake_preview, set=BakePreview.set_bake_preview)
    preview_type = "Preview w/ Alpha"
    # Can only be one, even if there are multiple ImageLayers, since making one materialOutput active would inactivate others


class ImageLayers_Controller(PropertyGroup):
    def name_format(self, node, sub=False):
        return f"{'        ' if sub else ''}{node.name}"

    def set_target_node_group(self, value):
        self['_target_node_group'] = _node_groups[value][0]

    def set_target_node_group_string(self, value):
        self['_target_node_group'] = value

    target_node_group: EnumProperty(name="Target Group Node", items=callback_target_node_group,
                                    set=set_target_node_group)


class ImageLayer_CollT(PropertyGroup):
    name: StringProperty()
    parent_node_group: StringProperty()
    node_mix_group: StringProperty()

    def get_is_hidden(self):
        return (bpy.data.node_groups[self.parent_node_group].nodes[self.node_mix_group].inputs['<Internal> Visibility'].default_value == 0)

    def set_is_hidden(self, value):
        bpy.data.node_groups[self.parent_node_group].nodes[self.node_mix_group].inputs['<Internal> Visibility'].default_value = 0 if value else 1

    is_hidden: BoolProperty(name="", description="Hide layer", get=get_is_hidden, set=set_is_hidden)


class ImageLayers(PropertyGroup):
    # Used in property storage node. This stores all properties for a image layers node group
    # The node group's node tree is self.id_data

    def update_active_index(self, context):
        if (node_tex := self.get_layer_node('IMG_TEX')):
            if (image := node_tex.image):

                mat = context.object.active_material
                if (index := mat.texture_paint_slots.find(image.name)) == -1:
                    mats = context.object.data.materials
                    mats.append(None)
                    mats.pop()
                    # above + below empty operator to refresh texture_paint_slots; Blender 4.1
                    bpy.ops.utils.dummy()

                    index = mat.texture_paint_slots.find(image.name)
                mat.paint_active_slot = index

    def get_layer_id(self, index):
        len_ = len(self.items)
        if (index < 0) or (index > len_):
            return index
        return (len_ - 1) - index

    def get_layer_node(self, node_type, index=None, l_id=None):
        if index is not None:
            l_id = self.get_layer_id(index)
        elif index is None and l_id is None:
            l_id = self.get_layer_id(self.active_index)

        match node_type:
            case 'IMG_TEX':
                node_name = f"DoNotChange_SourceImage_{l_id:03}"
            case 'MIX_GROUP':
                node_name = f"DoNotChange_MixGroup_{l_id:03}"
            case 'FRAME':
                node_name = f"DoNotChange_Frame_{l_id:03}"
        return self.id_data.nodes.get(node_name)

    items: CollectionProperty(type=ImageLayer_CollT)
    active_index: IntProperty(name="If pop-up panel, Ctrl + Double click, else", update=update_active_index)


class ImageLayers_Panel_Dock(PropertyGroup):
    def callback_mode(self, context):
        _image_layers_panel_dock_mode.clear()
        _image_layers_panel_dock_mode.append(('DOCK', "Dock", ""))
        if hasattr(bpy.types, "MXD_PT_PaintTexture_ImageLayersPanel_Dock"):
            _image_layers_panel_dock_mode.append(('REMOVE', "Remove", ""))
        return _image_layers_panel_dock_mode

    docked: BoolProperty()
    mode: EnumProperty(items=callback_mode)
    bl_space_type: EnumProperty(items=[('VIEW_3D', "3D Viewport", ""),
                                       ('PROPERTIES', "Properties", "")],
                                name="Space Type")
    bl_region_type: EnumProperty(items=[('UI', "N Panel", "")],
                                 name="Region Type")
    bl_category: EnumProperty(items=[('Item', "Item", ""),
                                     ('Tool', "Tool", ""),
                                     ('View', "View", ""),
                                     ('CUSTOM', "Custom", "")],
                              default='CUSTOM',
                              name="Tab")
    custom_category: StringProperty(name="", default="Image Layers",
                                    description="Append to an existing tab, or make a new one")
    bl_context: EnumProperty(items=[('object', "Object Properties", "", 'OBJECT_DATA', 0),
                                    ('physics', "Physics Properties", "", 'PHYSICS', 1),
                                    ('constraint', "Object Constraint Properties", "", 'CONSTRAINT', 2),
                                    ('data', "Object Data Properties", "", 'ARMATURE_DATA', 3),
                                    ('material', "Material Properties", "", 'MATERIAL_DATA', 4)],
                             name="Tab")
    bl_label: StringProperty(name="", default="Image Layers")


@persistent
def save_images_on_file_save(_):
    op = bpy.ops.image.save_all_modified
    if op.poll():
        op()
        pref = bpy.context.preferences.addons[__package__.partition(".")[0]].preferences
        pnl = pref.image_layers_panel.dock
        for area in bpy.context.screen.areas:
            match area.type:
                case pnl.bl_space_type if pnl.docked:
                    match area.type:
                        case 'VIEW_3D':
                            if bpy.context.space_data.show_region_ui:
                                for region in area.regions:
                                    if region.type == 'UI':
                                        region.tag_redraw()
                                        break
                        case 'PROPERTIES':
                            if area.spaces[0].context == pnl.bl_context.upper():
                                for region in area.regions:
                                    if region.type == 'WINDOW':
                                        region.tag_redraw()
                                        break
                case 'IMAGE_EDITOR':
                    for region in area.regions:
                        if region.type == 'HEADER':
                            region.tag_redraw()
                            break


class ImageLayers_Panel_Preset_NewImage(PropertyGroup):
    def update_mode(self, context):
        op = context.window_manager.operator_properties_last("image.new")
        op.width = op.height = int(self.dimensions)
        op.color = self.color

    mode: EnumProperty(items=[('PRESET', "Preset", ""), ('CUSTOM', "Custom", "")], update=update_mode)

    DIMENSIONS = [
        ('256', "256 x 256", ""),
        ('512', "512 x 512", ""),
        ('1024', "1024 x 1024", ""),
        ('2048', "2048 x 2048", ""),
        ('4096', "4096 x 4096", ""),
        ('8192', "8192 x 8192", ""),
    ]

    dimensions: EnumProperty(name="DImensions", items=DIMENSIONS, default='2048')
    color: FloatVectorProperty(name="Color", size=4, subtype='COLOR', min=0, max=1)


class ImageLayers_Panel(PropertyGroup):
    ui_units_x: FloatProperty(name="", description="Horizontal size of the panel",
                              default=13, min=10, soft_max=30, max=50, step=25)
    show_ui_units_x: BoolProperty(name="Panel Horizontal Size")
    is_target_node_group_expanded: BoolProperty(name="Target Controller", default=True)
    is_layer_setting_expanded: BoolProperty(name="", default=True)
    is_next_node_expanded: BoolProperty(name="", default=True)

    show_layer_id: BoolProperty(name="Show layers ID", default=True)

    dock: PointerProperty(type=ImageLayers_Panel_Dock)
    # from .bake_image_layers_prop import ImageLayers_BakeSettings
    # bake_settings: PointerProperty(type=ImageLayers_BakeSettings)
    preset_new_image: PointerProperty(type=ImageLayers_Panel_Preset_NewImage)

    def update_save_images(self, context):
        exists = (save_images_on_file_save in save_pre)
        if self.save_images_on_file_save and not exists:
            save_pre.append(save_images_on_file_save)
        else:
            if exists:
                save_pre.remove(save_images_on_file_save)

    save_images_on_file_save: BoolProperty(name="Save all modified images on file save", update=update_save_images)


classes = (
    Material_ImageLayers,
    ImageLayers_Controller,
    ImageLayer_CollT,
    ImageLayers,
    ImageLayers_Panel_Dock,
    ImageLayers_Panel_Preset_NewImage,
    ImageLayers_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    Material.image_layers = PointerProperty(type=Material_ImageLayers)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del Material.image_layers
