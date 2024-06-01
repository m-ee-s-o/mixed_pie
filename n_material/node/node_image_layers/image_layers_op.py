import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty
from bpy.app.handlers import save_pre
from bpy.utils import register_class, unregister_class
from ..node_utils import get_node_space
from . import image_layers_ui
from .image_layers_prop import save_images_on_file_save
from .image_layers_ui import Base_ImageLayersPanel


def make_mix_group():
    node_groups = bpy.data.node_groups
    if "MixGroup" in node_groups:
        return node_groups['MixGroup']

    node_tree = node_groups.new("MixGroup", 'ShaderNodeTree')
    interface = node_tree.interface
    nodes = node_tree.nodes
    links = node_tree.links

    interface.new_socket(name="Image", in_out='INPUT', socket_type='NodeSocketColor')
    i_alpha = interface.new_socket(name="Alpha", in_out='INPUT', socket_type='NodeSocketColor')
    i_alpha.default_value = (1, 1, 1, 1)
    i_alpha.hide_value = True

    interface.new_socket(name="[Prior] Image", in_out='INPUT', socket_type='NodeSocketColor')
    i_prior_alpha = interface.new_socket(name="[Prior] Alpha", in_out='INPUT', socket_type='NodeSocketColor')
    i_prior_alpha.hide_value = True

    i_opacity_slider = interface.new_socket(name="Opacity", in_out='INPUT', socket_type='NodeSocketFloat')
    i_opacity_slider.subtype = 'FACTOR'
    i_opacity_slider.default_value = 1
    i_opacity_slider.min_value = 0
    i_opacity_slider.max_value = 1

    i_use_prior_alpha = interface.new_socket(name="<Internal> Use Prior Alpha", in_out='INPUT', socket_type='NodeSocketFloat')
    i_use_prior_alpha.hide_value = True
    i_use_prior_alpha.subtype = 'FACTOR'

    i_visibility_switch = interface.new_socket(name="<Internal> Visibility", in_out='INPUT', socket_type='NodeSocketFloat')
    i_visibility_switch.hide_value = True
    i_visibility_switch.default_value = 1
    i_visibility_switch.subtype = 'FACTOR'

    interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
    interface.new_socket(name="Alpha", in_out='OUTPUT', socket_type='NodeSocketColor')

    X_SPACE, Y_SPACE = get_node_space()
    HEIGHT_MIX_NODE = 222
    HEIGHT_GROUP_INPUT_NODE = 204

    input_node = nodes.new('NodeGroupInput')

    visibility_switch = nodes.new(type='ShaderNodeMath')
    visibility_switch.operation = 'MULTIPLY'
    visibility_switch.location.x = input_node.width + X_SPACE
    visibility_switch.location.y -= HEIGHT_GROUP_INPUT_NODE + Y_SPACE

    use_prior_alpha = nodes.new(type='ShaderNodeMix')
    use_prior_alpha.data_type = 'RGBA'
    use_prior_alpha.blend_type = 'MULTIPLY'
    use_prior_alpha.location = visibility_switch.location
    use_prior_alpha.location.x += visibility_switch.width + X_SPACE

    opacity_slider = nodes.new(type='ShaderNodeMath')
    opacity_slider.operation = 'MULTIPLY'
    opacity_slider.location = use_prior_alpha.location
    opacity_slider.location.x += use_prior_alpha.width + X_SPACE

    invert_prior_alpha = nodes.new(type='ShaderNodeInvert')
    invert_prior_alpha.location = opacity_slider.location
    invert_prior_alpha.location.x += opacity_slider.width + X_SPACE

    multiply_alphas = nodes.new(type='ShaderNodeMath')
    multiply_alphas.operation = 'MULTIPLY'
    multiply_alphas.location = invert_prior_alpha.location
    multiply_alphas.location.x += invert_prior_alpha.width + X_SPACE

    add_alphas = nodes.new(type='ShaderNodeMath')
    add_alphas.location = multiply_alphas.location
    add_alphas.location.x += multiply_alphas.width + X_SPACE

    mix = nodes.new(type='ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.location.x = multiply_alphas.location.x + multiply_alphas.width + X_SPACE
    mix.location.y = multiply_alphas.location.y + HEIGHT_MIX_NODE + Y_SPACE

    output_node = nodes.new('NodeGroupOutput')
    output_node.location.x = mix.location.x + mix.width + X_SPACE

    links.new(input_node.outputs['Image'], mix.inputs[7])
    links.new(input_node.outputs['Alpha'], use_prior_alpha.inputs[6])
    links.new(input_node.outputs['[Prior] Image'], mix.inputs[6])
    links.new(input_node.outputs['[Prior] Alpha'], use_prior_alpha.inputs[7])
    links.new(input_node.outputs['[Prior] Alpha'], multiply_alphas.inputs[1])
    links.new(input_node.outputs['Opacity'], visibility_switch.inputs[0])
    links.new(input_node.outputs['<Internal> Use Prior Alpha'], use_prior_alpha.inputs['Factor'])
    links.new(input_node.outputs['<Internal> Visibility'], visibility_switch.inputs[1])

    links.new(visibility_switch.outputs['Value'], opacity_slider.inputs[1])
    links.new(use_prior_alpha.outputs[2], opacity_slider.inputs[0])
    links.new(opacity_slider.outputs['Value'], mix.inputs['Factor'])
    links.new(opacity_slider.outputs['Value'], invert_prior_alpha.inputs['Color'])
    links.new(opacity_slider.outputs['Value'], add_alphas.inputs[1])
    links.new(invert_prior_alpha.outputs['Color'], multiply_alphas.inputs[0])
    links.new(multiply_alphas.outputs['Value'], add_alphas.inputs[0])
    links.new(add_alphas.outputs['Value'], output_node.inputs['Alpha'])
    links.new(mix.outputs[2], output_node.inputs['Color'])

    for node in nodes:
        node.select = False

    return node_tree


class MXD_OT_ImageLayers_Operations(Operator):
    bl_idname = "image_layers.operations"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    mode: StringProperty(options={'HIDDEN'})
    target_node_group: StringProperty(options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'ADD_NODE_GROUP':
                return "Add node group"
            case 'REMOVE_NODE_GROUP':
                return "Remove node group"
            case 'ADD':
                return "Add another layer.\n\n"  \
                       "Shift: Also add image texture"
            case 'REMOVE':
                return "Remove layer"
            case 'MOVE_UP':
                return "Move up"
            case 'MOVE_DOWN':
                return "Move down"

    def invoke(self, context, event):
        if self.mode == 'ADD':
            self.shift = event.shift
        return self.execute(context)

    def execute(self, context):
        X_SPACE, Y_SPACE = get_node_space()
        FRAME_HEIGHT = 337

        node_groups = bpy.data.node_groups
        mat = context.object.active_material
        node_group = mat.node_tree.nodes.get(self.target_node_group)
        if not node_group or (node_group and (node_group.bl_idname != 'ShaderNodeGroup')):
            return {'CANCELLED'}
        if self.mode != 'ADD_NODE_GROUP':
            node_tree = node_group.node_tree
            nodes = node_tree.nodes
            if (prop_storage := nodes.get("DoNotChange_PropertyStorage")):
                layers = prop_storage.layers
                active_index = layers.active_index

        match self.mode:
            case 'ADD_NODE_GROUP':
                MIX_GROUP_WIDTH = 210
                GROUP_OUTPUT_HEIGHT = 99

                node_tree = node_groups.new("ImageLayers", 'ShaderNodeTree')
                nodes = node_tree.nodes
                interface = node_tree.interface

                interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
                interface.new_socket(name="Alpha", in_out='OUTPUT', socket_type='NodeSocketColor')

                group_output = nodes.new('NodeGroupOutput')
                group_output.name = "DoNotChange_GroupOutput"
                group_output.location.x = MIX_GROUP_WIDTH + (X_SPACE * 2)

                prop_storage = nodes.new('PropStorage')
                prop_storage.name = "DoNotChange_PropertyStorage"
                prop_storage.location.x = group_output.location.x
                prop_storage.location.y -= GROUP_OUTPUT_HEIGHT + (Y_SPACE / 3)
                prop_storage.hide = True

                for node in nodes:
                    node.select = False

                node_group.node_tree = node_tree

                image_layers = mat.image_layers
                if image_layers.target_node_group == "—":
                    image_layers.target_node_group = node_group.name
                    pref = context.preferences.addons[__package__.partition(".")[0]].preferences
                    pref.image_layers_panel.is_target_node_group_expanded = False
            case 'REMOVE_NODE_GROUP':
                if prop_storage:
                    for node in nodes:
                        if node.name.startswith("DoNotChange_MixGroup") and node.node_tree:
                            node_groups.remove(node.node_tree)
                node_groups.remove(node_tree)
                node_group.node_tree = None

            case 'ADD':
                layer = layers.items.add()
                default_name, suffix_counter = "Layer", 0
                name = default_name
                layer_names = {layer_item.name
                               for layer_item in layers.items
                               if layer_item.name.startswith("Layer")}
                while True:
                    if name in layer_names:
                        suffix_counter += 1
                        name = f"{default_name}.{suffix_counter:03}"
                    else:
                        break

                layer.name = name
                len_layers = len(layers.items)
                layers.items.move(len_layers - 1, active_index)

                mix_group = make_mix_group()

                node_mix_group = nodes.new('ShaderNodeGroup')
                node_mix_group.node_tree = mix_group
                node_mix_group.width *= 1.5

                node_img_tex = nodes.new(type='ShaderNodeTexImage')
                node_img_tex.location.x -= node_img_tex.width + X_SPACE

                new_frame = nodes.new('NodeFrame')
                node_mix_group.parent = new_frame
                node_img_tex.parent = new_frame

                is_top_layer = (active_index == 0)

                node_tree.links.new(node_img_tex.outputs['Color'], node_mix_group.inputs['Image'])
                node_tree.links.new(node_img_tex.outputs['Alpha'], node_mix_group.inputs['Alpha'])
                if is_top_layer and (node_group_output := node_tree.nodes.get("DoNotChange_GroupOutput")):
                    node_tree.links.new(node_mix_group.outputs['Color'], node_group_output.inputs['Color'])
                    node_tree.links.new(node_mix_group.outputs['Alpha'], node_group_output.inputs['Alpha'])

                for index in range(len_layers):
                    layer = layers.items[index]
                    l_id = layers.get_layer_id(index)
                    if index < active_index:  # Increment suffixes
                        frame = nodes[f"DoNotChange_Frame_{l_id - 1:03}"]
                        frame.name = f"DoNotChange_Frame_{l_id:03}"
                        if frame.label == f"{l_id - 1:03}":
                            frame.label = f"{l_id:03}"

                        if (node := nodes.get(f"DoNotChange_SourceImage_{l_id - 1:03}")):
                            node.name = f"DoNotChange_SourceImage_{l_id:03}"

                        node = nodes[f"DoNotChange_MixGroup_{l_id - 1:03}"]
                        node.name = f"DoNotChange_MixGroup_{l_id:03}"
                        layer.node_mix_group = node.name
                    elif index >= active_index:
                        if index == active_index:  # Set names for new layer
                            node_mix_group.name = f"DoNotChange_MixGroup_{l_id:03}"
                            layer.parent_node_group = node_tree.name
                            layer.node_mix_group = node_mix_group.name

                            node_img_tex.name = f"DoNotChange_SourceImage_{l_id:03}"

                            new_frame.name = f"DoNotChange_Frame_{l_id:03}"
                            new_frame.label = f"{l_id:03}"
                            new_frame.label_size = 14
                            if is_top_layer:
                                continue

                        below = nodes[f"DoNotChange_MixGroup_{l_id:03}"]
                        above = nodes[f"DoNotChange_MixGroup_{l_id + 1:03}"]
                        node_tree.links.new(below.outputs['Color'], above.inputs['[Prior] Image'])
                        node_tree.links.new(below.outputs['Alpha'], above.inputs['[Prior] Alpha'])

                        frame = nodes[f"DoNotChange_Frame_{l_id:03}"]
                        frame.location.y = -(FRAME_HEIGHT + Y_SPACE) * index

                for node in nodes:
                    node.select = False

                if getattr(self, "shift", None):
                    bpy.ops.image.new_using_preset('INVOKE_DEFAULT')
            case 'REMOVE':
                l_id = layers.get_layer_id(active_index)
                if (frame := nodes.get(f"DoNotChange_Frame_{l_id:03}")):
                    for node in nodes:
                        if node.parent and (node.parent.name == frame.name):
                            nodes.remove(node)
                    nodes.remove(frame)
                else:
                    if (mix_group := nodes.get(f"DoNotChange_MixGroup_{l_id:03}")):
                        node_groups.remove(mix_group.node_tree)
                        nodes.remove(mix_group)
                    if (node_img_tex := nodes.get(f"DoNotChange_SourceImage_{l_id:03}")):
                        nodes.remove(node_img_tex)

                layers.items.remove(active_index)

                len_layers = len(layers.items)
                deleted_top_layer = (active_index == 0)
                deleted_bottom_layer = (active_index == len_layers)
                active_index = max(0, min(len_layers - 1, active_index))

                start = active_index - (0 if deleted_bottom_layer else 1)

                # Loop is done by index in layers.items (e.g., 5 to 0, of 9) but since layer_id/l_id is inverse,...
                # ... it goes up and inversed in layer_id's terms (e.g., 4 to 9, of 9) and decrements suffixes above the deleted layer.
                for index in range(start, -1, -1):
                    layer = layers.items[index]
                    l_id = layers.get_layer_id(index)
                    if node := nodes.get(f"DoNotChange_Frame_{l_id + 1:03}"):
                        node.name = f"DoNotChange_Frame_{l_id:03}"
                        if node.label == f"{l_id + 1:03}":
                            node.label = f"{l_id:03}"

                    if (node := nodes.get(f"DoNotChange_SourceImage_{l_id + 1:03}")):
                        node.name = f"DoNotChange_SourceImage_{l_id:03}"

                    if (node := nodes.get(f"DoNotChange_MixGroup_{l_id + 1:03}")):
                        node.name = f"DoNotChange_MixGroup_{l_id:03}"
                        layer.node_mix_group = node.name

                for index in range(active_index, len_layers):  # Bridge new links and overwrite existing ones
                    l_id = layers.get_layer_id(index)
                    if (active := nodes.get(f"DoNotChange_MixGroup_{l_id:03}")):
                        if ((deleted_top_layer and (index == active_index))
                                or len_layers == 1):
                            above = nodes["DoNotChange_GroupOutput"]
                            inputs = ('Color', 'Alpha')
                        else:
                            above = nodes[f"DoNotChange_MixGroup_{l_id + 1:03}"]
                            inputs = ('[Prior] Image', '[Prior] Alpha')
                        node_tree.links.new(active.outputs['Color'], above.inputs[inputs[0]])
                        node_tree.links.new(active.outputs['Alpha'], above.inputs[inputs[1]])

                    if (frame := nodes.get(f"DoNotChange_Frame_{l_id:03}")):
                        frame.location.y = -(FRAME_HEIGHT + Y_SPACE) * index

                layers.active_index = active_index
            case 'MOVE_UP':
                self.move(layers, nodes, node_tree, up=True)
            case 'MOVE_DOWN':
                self.move(layers, nodes, node_tree)
        return {'FINISHED'}

    def move(self, layers, nodes, node_tree, up=False):
        items = layers.items
        active_index = layers.active_index
        to = active_index + (-1 if up else 1)
        id_to = layers.get_layer_id(to)
        id_active = layers.get_layer_id(active_index)

        frame_to = nodes[f"DoNotChange_Frame_{id_to:03}"]
        frame_active = nodes[f"DoNotChange_Frame_{id_active:03}"]
        frame_active.location.y, frame_to.location.y = frame_to.location.y, frame_active.location.y
        frame_active.label, frame_to.label = frame_to.label, frame_active.label
        self.swap(frame_to, frame_active, "name")

        img_to = nodes[f"DoNotChange_SourceImage_{id_to:03}"]
        img_active = nodes[f"DoNotChange_SourceImage_{id_active:03}"]
        self.swap(img_to, img_active, "name")

        inner_group_to = nodes[f"DoNotChange_MixGroup_{id_to:03}"]
        inner_group_active = nodes[f"DoNotChange_MixGroup_{id_active:03}"]
        self.swap(inner_group_to, inner_group_active, "name")
        self.swap(items[to], items[active_index], "node_mix_group")
        if (inner_group_to.node_tree.name.startswith(f"~ {id_to:03}")
                and inner_group_active.node_tree.name.startswith(f"~ {id_active:03}")):
            self.swap(inner_group_to.node_tree, inner_group_active.node_tree, "name")

        if not up:
            inner_group_to, inner_group_active = inner_group_active, inner_group_to

        for input, output in (('[Prior] Image', 'Color'),   # Swap links
                              ('[Prior] Alpha', 'Alpha')):
            i_active = inner_group_active.inputs[input]
            o_to = inner_group_to.outputs[output]
            o_active = inner_group_active.outputs[output]
            o_links_to = [(link.to_node, link.to_socket.name) for link in o_to.links]
            i_links_active = [link.from_node for link in i_active.links]
            for i in (o_to, o_active):
                for link in i.links:
                    node_tree.links.remove(link)
            for node, socket in o_links_to:
                node_tree.links.new(inner_group_active.outputs[output], node.inputs[socket])
            if i_links_active:
                node_tree.links.new(i_links_active[0].outputs[output], inner_group_to.inputs[input])
            node_tree.links.new(o_to, i_active)

        items.move(active_index, to)
        layers.active_index = to

    def swap(self, this, that, attr):
        to_this = getattr(this, attr)
        to_that = getattr(that, attr)
        setattr(this, attr, "")
        setattr(that, attr, "")
        setattr(this, attr, to_that)
        setattr(that, attr, to_this)


class MXD_OT_ImageLayers_AddNextNode(Operator):
    bl_idname = "image_layers.add_next_node"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Add node next to image texture node"

    type: StringProperty(options={'HIDDEN'})
    node_group: StringProperty(options={'HIDDEN'})
    image_texture_node: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        node_tree = bpy.data.node_groups[self.node_group]
        nodes = node_tree.nodes
        links = node_tree.links

        img_tex = nodes[self.image_texture_node]

        for output in img_tex.outputs:
            if output.is_linked:
                link = output.links[0]
                current_next_node = link.to_node
                to_socket = link.to_socket
                break
        else:
            return {'CANCELLED'}

        frame = current_next_node.parent
        current_next_node.parent = None

        new_node = nodes.new(type=self.type)
        new_node.select = False
        X_SPACE, _ = get_node_space()
        new_node.location = current_next_node.location
        new_node.location.x -= new_node.width + X_SPACE
        img_tex.location.x = new_node.location.x - img_tex.width - X_SPACE

        current_next_node.parent = new_node.parent = frame

        match self.type:
            case 'ShaderNodeHueSaturation':
                links.new(new_node.outputs['Color'], to_socket)
                links.new(img_tex.outputs['Color'], new_node.inputs['Color'])

        new_node.inputs[0].show_expanded = True

        return {'FINISHED'}


class MXD_OT_ImageLayersPanel_Info(Operator):
    bl_idname = "image_layers_panel.info"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = "Info"

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        col_m = layout.box().column()
        col_m.label(text="Info")

        col = col_m.column(align=True)
        col.label(text='—    Panel horizontal size, "Show layers ID", and')
        col.label(text="       dock settings are stored in preferences.")
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="       Be sure to")
        row.operator("wm.save_userpref")
        row.label(text=" .")

        row = col_m.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="—    This panel can be")
        row.operator("image_layers_panel.dock", text="docked")
        row.label(text=" to somewhere.")

    def execute(self, context):
        return {'CANCELLED'}


def make_pnl_class():
    cls = type(
        "MXD_PT_PaintTexture_ImageLayersPanel_Dock",
        (Base_ImageLayersPanel, Panel),
        {"docked": True}
    )
    return cls


class MXD_OT_ImageLayersPanel_Dock(Operator):
    bl_idname = "image_layers_panel.dock"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = "Dock image layers panel to somewhere"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        pnl = pref.image_layers_panel.dock

        layout = self.layout
        row = layout.row()
        split = row.split(factor=1 if hasattr(bpy.types, "MXD_PT_PaintTexture_ImageLayersPanel_Dock") else 1/2)
        split.row().prop(pnl, "mode", expand=True)

        if pnl.mode == 'DOCK':
            col = layout.column()
            col.use_property_split = True
            col.use_property_decorate = False

            col.prop(pnl, "bl_label", text="Panel Name")
            col.prop(pnl, "bl_space_type")
            if pnl.bl_space_type == 'VIEW_3D':
                col.prop(pnl, "bl_region_type")
                col.prop(pnl, "bl_category")
                if pnl.bl_category == 'CUSTOM':
                    col.prop(pnl, "custom_category", text="Tab Name")
            else:
                col.prop(pnl, "bl_context")

    def execute(self, context):
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        pnl = pref.image_layers_panel.dock

        if (cls := getattr(bpy.types, "MXD_PT_PaintTexture_ImageLayersPanel_Dock", None)):
            if pnl.mode == 'REMOVE':
                pnl.docked = False
                pnl.mode = 'DOCK'
                unregister_class(cls)
                return {'FINISHED'}
            unregister_class(cls)

        MXD_PT_PaintTexture_ImageLayersPanel_Dock = make_pnl_class()

        pnl.docked = True
        if pnl.bl_space_type == 'VIEW_3D':
            region_type = pnl.bl_region_type
            category = pnl.bl_category if (pnl.bl_category != 'CUSTOM') else pnl.custom_category
            MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_category = category
        else:
            region_type = 'WINDOW'
            MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_context = pnl.bl_context

        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_label = pnl.bl_label
        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_space_type = pnl.bl_space_type
        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_region_type = region_type
        register_class(MXD_PT_PaintTexture_ImageLayersPanel_Dock)
        return {'FINISHED'}


class MXD_OT_Image_NewUsingPreset(Operator):
    bl_idname = "image.new_using_preset"
    bl_label = "New Image"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "New Image\n"         \
                     "Create a new image"

    props = ("name", "width", "height", "color", "alpha", "generated_type", "float", "tiled")

    def invoke(self, context, event):
        self.done = False
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        if self.done:
            return
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        pni = pref.image_layers_panel.preset_new_image

        layout = self.layout
        layout.prop(pni, "mode", expand=True)

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        op = context.window_manager.operator_properties_last("image.new")
        match pni.mode:
            case 'PRESET':
                col.prop(pni, "dimensions")
                col.prop(pni, "color")
            case 'CUSTOM':
                # props = [prop for prop in op.rna_type.properties]
                for prop in self.props:
                    col.prop(op, prop)

    def execute(self, context):
        self.done = True
        self.new_image(context, image_layers_ui.active_image_node)
        # image_layers_ui.active_image_node --- Defined in image_layers_ui.Base_DrawButtons.draw_layer_properties
        return {'FINISHED'}

    @classmethod
    def new_image(cls, context: bpy.types.Context, node, kwargs=None):
        if not kwargs:
            pref = context.preferences.addons[__package__.partition(".")[0]].preferences
            pni = pref.image_layers_panel.preset_new_image

            op = context.window_manager.operator_properties_last("image.new")
            if pni.mode == 'PRESET':
                op.width = op.height = int(pni.dimensions)
                op.color = pni.color
            kwargs = {prop: getattr(op, prop) for prop in cls.props}

        pre_images = set(bpy.data.images)

        # NOTE: Seems like if calling ops, params should be passed, whereas it's fine not to if layout.operator()
        bpy.ops.image.new(**kwargs)

        post_images = set(bpy.data.images)
        new = tuple(post_images.difference(pre_images))[0]

        node.image = new

        image_layers_ui.image_layers.update_active_index(context)


classes = (
    MXD_OT_ImageLayers_Operations,
    MXD_OT_ImageLayers_AddNextNode,
    MXD_OT_ImageLayersPanel_Info,
    MXD_OT_ImageLayersPanel_Dock,
    MXD_OT_Image_NewUsingPreset,
)


def register():
    pref = bpy.context.preferences.addons[__package__.partition(".")[0]].preferences
    image_layers = pref.image_layers_panel
    pnl = image_layers.dock
    if pnl.docked:
        MXD_PT_PaintTexture_ImageLayersPanel_Dock = make_pnl_class()

        if pnl.bl_space_type == 'VIEW_3D':
            region_type = pnl.bl_region_type
            category = pnl.bl_category if (pnl.bl_category != 'CUSTOM') else pnl.custom_category
            MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_category = category
        else:
            region_type = 'WINDOW'
            MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_context = pnl.bl_context

        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_label = pnl.bl_label
        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_space_type = pnl.bl_space_type
        MXD_PT_PaintTexture_ImageLayersPanel_Dock.bl_region_type = region_type
        register_class(MXD_PT_PaintTexture_ImageLayersPanel_Dock)

    for cls in classes:
        register_class(cls)

    if image_layers.save_images_on_file_save:
        save_pre.append(save_images_on_file_save)


def unregister():
    for cls in classes:
        unregister_class(cls)

    if (cls := getattr(bpy.types, "MXD_PT_PaintTexture_ImageLayersPanel_Dock", None)):
        unregister_class(cls)

    if save_images_on_file_save in save_pre:
        save_pre.remove(save_images_on_file_save)
