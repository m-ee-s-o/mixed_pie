import bpy
from bpy.types import Menu, Node, Panel, UIList
from bpy.props import PointerProperty
from .image_layers_prop import ImageLayers, ImageLayers_Controller, save_images_on_file_save
from .bake_preview import BakePreview


class MXD_UL_Materials_ImageLayers(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            pref = context.preferences.addons[__package__.partition(".")[0]].preferences
            panel = pref.image_layers_panel
            l_id = data.get_layer_id(index)
            node_group_mix = data.get_layer_node('MIX_GROUP', l_id=l_id)

            row = layout.row()
            s1_row = row.row(align=True)

            if panel.show_layer_id:
                s2_row = row.row()
                s2_row.alignment = 'RIGHT'
                s2_row.enabled = False
                s2_row.label(text=f"{l_id:03}")
            s3_row = row.row(align=True)

            if ((node_img_tex := data.get_layer_node('IMG_TEX', l_id=l_id))
                    and not node_img_tex.mute
                    and (image := node_img_tex.image)):
                mat = context.object.active_material
                if context.mode == 'PAINT_TEXTURE'                                              \
                        and mat.texture_paint_slots[mat.paint_active_slot].name == image.name:
                    icon = 'TPAINT_HLT'
                else:
                    icon = 'BLANK1'
                s1_row.label(icon=icon)
                s1_row.prop(image, "name", text="", emboss=False)
            else:
                s1_row.label(icon='BLANK1')
                s1_row.prop(item, "name", text="", emboss=False)

            if node_group_mix:
                s3_row1 = s3_row.row()
                s3_row2 = s3_row.row()

                # # Not Needed if there's no bake feature
                # TODO: change
                # node = data.get_layer_node('USE_PRIOR_ALPHA', l_id=l_id)
                # op = s3_row1.operator("utils.properties_toggle_description", emboss=False,
                #                         icon='MOD_UVPROJECT' if not node.mute else 'CHECKBOX_DEHLT')
                # op.parent = repr(node)
                # op.prop = "mute"
                # op.description = "Use alpha of the layer below instead of own alpha"

                s1_row.enabled = s3_row1.enabled = not item.is_hidden
                s3_row2.prop(item, "is_hidden", emboss=False, icon='HIDE_ON' if item.is_hidden else 'HIDE_OFF')

            else:
                s3_row.label(icon='BLANK1')
                s3_row.label(icon='BLANK1')

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(icon='GROUP')


class MXD_Node_ImageLayers_PropStorage(Node):
    bl_idname = 'PropStorage'
    bl_label = "Property Storage"

    layers: PointerProperty(type=ImageLayers)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.separator(factor=1.2)
        row.label(text="Important")


class Base_DrawButtons:
    @classmethod
    def invoke(cls, context, layout, parent_data_of_target_node_group, controller=None):
        pref = bpy.context.preferences.addons[__package__.partition(".")[0]].preferences
        panel = pref.image_layers_panel

        target_node_group = parent_data_of_target_node_group.target_node_group
        mat = context.object.active_material
        node_group = mat.node_tree.nodes.get(target_node_group)

        if not node_group:
            layout.alert = True
            layout.prop(parent_data_of_target_node_group, "target_node_group", text="")
            return

        BakePreview.node_group = node_group
        mat.image_layers.is_preview_shown  # Check validity

        SPACE = 0.75
        node_tree = node_group.node_tree

        col_m = layout.column()
        row_m = col_m.row()

        if controller:
            row_m.template_ID(node_group, "node_tree")

            row = row_m.row(align=True)
            row.alignment = 'RIGHT'
            op = row.operator("image_layers.operations", icon='ADD')
            op.mode = 'ADD_NODE_GROUP'
            op.target_node_group = target_node_group

            s_row = row.row()
            s_row.enabled = True if node_tree else False
            op = s_row.operator("image_layers.operations", icon='REMOVE')
            op.mode = 'REMOVE_NODE_GROUP'
            op.target_node_group = target_node_group

        if not node_tree:
            if not controller:
                layout.alert = True
                layout.label(text="Node group hasn't been set. Go to node editor.")
        else:
            if controller:
                col_m.separator(factor=SPACE)

            nodes = node_tree.nodes

            name_output_node = "DoNotChange_GroupOutput"
            if not nodes.get(name_output_node):
                layout.alert = True
                layout.label(text=f'Node "{name_output_node}" not found.')
                return

            name_prop_storage_node = "DoNotChange_PropertyStorage"
            prop_storage = nodes.get(name_prop_storage_node)
            if not prop_storage:
                layout.alert = True
                layout.label(text=f'Node "{name_prop_storage_node}" not found.')
                return

            layers = prop_storage.layers
            items = layers.items

            # for item in items:
            #     layout.label(text=item.node_mix_group)

            missing_nodes = []
            len_ = len(items)
            for i in range(len_):
                l_id = layers.get_layer_id(i)
                for node in (f"DoNotChange_MixGroup_{l_id:03}", f"DoNotChange_Frame_{l_id:03}"):
                    if not nodes.get(node):
                        missing_nodes.append(node)

            disabled = True if missing_nodes else False
            cls.draw_layer_list(col_m, layers, items, node_tree, target_node_group, len_, disabled)

            for node in missing_nodes:
                row = layout.row()
                row.alert = True
                row.label(text=f'Node "{node}" not found.')

            if missing_nodes or not items:
                return

            col_m.separator(factor=SPACE)

            node_group_mix = layers.get_layer_node('MIX_GROUP')
            node_img_tex = layers.get_layer_node('IMG_TEX')
            active_layer = layers.items[layers.active_index]

            icon = 'FILE_REFRESH' if (save_images_on_file_save in bpy.app.handlers.save_pre) else 'FILE_TICK'
            col_m.operator("image.save_all_modified", text="Save All Images", icon=icon)
            col_m.separator(factor=SPACE)

            cls.draw_layer_properties(layout, SPACE, panel, node_img_tex, node_group_mix, active_layer)

    @classmethod
    def draw_layer_list(cls, col_m, layers, items, node_tree, target_node_group, len_, disabled):
        row = col_m.row()
        row.template_list("MXD_UL_Materials_ImageLayers", "",
                          layers, "items",
                          layers, "active_index")
        col = row.column(align=True)

        row = col.row()
        row.enabled = not disabled
        op = row.operator("image_layers.operations", icon='ADD')
        op.mode = 'ADD'
        op.target_node_group = target_node_group

        row = col.row()
        row.enabled = bool(items)
        op = row.operator("image_layers.operations", icon='REMOVE')
        op.mode = 'REMOVE'
        op.target_node_group = target_node_group

        col.separator()

        global node_group, image_layers
        node_group = node_tree
        image_layers = layers
        row = col.row()
        row.enabled = bool(items)
        row.menu("MXD_MT_Menu_ImageLayers", icon='DOWNARROW_HLT', text="")

        col.separator()

        row = col.row()
        row.enabled = True if (layers.active_index != 0) and not disabled else False
        op = row.operator("image_layers.operations", icon='TRIA_UP')
        op.mode = 'MOVE_UP'
        op.target_node_group = target_node_group

        row = col.row()
        row.enabled = True if (layers.active_index != max(0, (len_ - 1))) and not disabled else False
        op = row.operator("image_layers.operations", icon='TRIA_DOWN')
        op.mode = 'MOVE_DOWN'
        op.target_node_group = target_node_group

    @classmethod
    def draw_layer_properties(cls, layout, SPACE, panel, node_img_tex, node_mix_group, active_layer):
        col = layout.column()
        row = col.row()
        row.prop(panel, "is_layer_setting_expanded", icon_only=True, emboss=False,
                 icon='DOWNARROW_HLT' if panel.is_layer_setting_expanded else 'RIGHTARROW')

        if not panel.is_layer_setting_expanded and (node_img_tex and not node_img_tex.mute):
            text = node_img_tex.image.name if node_img_tex.image else "None"
            row.label(text=text)
            return

        if node_img_tex and not node_img_tex.mute:
            global active_image_node
            active_image_node = node_img_tex
            row.template_ID(node_img_tex, "image", new="image.new_using_preset", open="image.open")
        elif ((links := node_mix_group.inputs['Image'].links)
                and (node := links[0].from_node)
                and not node.mute
                and (name := node.name) != node_img_tex.name):
            row.label(text=name)
        else:
            row.prop(node_mix_group.inputs['Image'], "default_value", text="")                

        if node_img_tex and not node_img_tex.image:
            op = row.operator("utils.properties_toggle_description", emboss=False,
                                icon='IMAGE_DATA' if not node_img_tex.mute else 'COLORSET_13_VEC')
            op.parent = repr(node_img_tex)
            op.prop = "mute"
            op.description = "Toggle image or rgb for this layer"

        if (not panel.is_layer_setting_expanded
                or (node_img_tex and not (node_img_tex.image or node_img_tex.mute))):
            return

        col.separator(factor=SPACE)
        row1 = col.row()
        row1.active = not active_layer.is_hidden
        row1.label(icon='BLANK1')
        row1.prop(node_mix_group.inputs['Opacity'], "default_value", text="Opacity")
        if node_img_tex and not node_img_tex.image:
            row1.label(icon='BLANK1')

        if not (node_img_tex and node_img_tex.image):
            return

        cls.draw_next_nodes(layout, col, panel, node_img_tex)

    @classmethod
    def recur_get_next_nodes(cls, node, nodes=None):  # After image texture node
        if not nodes:
            nodes = []
        links_s = [output.links for output in node.outputs if output.is_linked]
        if not links_s:
            return nodes
        for links in links_s:
            for link in links:
                cur_node = link.to_node
                if cur_node in nodes:
                    continue
                if cur_node.inputs[-1].name == "<Internal> Visibility":
                    continue
                nodes.append(cur_node)
                cls.recur_get_next_nodes(cur_node, nodes)
        return nodes

    @classmethod
    def draw_next_nodes(cls, layout, col, panel, node_img_tex):
        col.separator(factor=0.01)
        nodes = cls.recur_get_next_nodes(node_img_tex)
        if not nodes:
            return

        col = layout.column()
        row = col.row()
        row.prop(panel, "is_next_node_expanded", icon_only=True, emboss=False,
                    icon='DOWNARROW_HLT' if panel.is_next_node_expanded else 'RIGHTARROW')
        row.label(text="Next Nodes")

        if panel.is_next_node_expanded:
            row = col.row()
            row.label(icon='BLANK1')
            col = row.box().column()

            len_ = len(nodes)
            for index, node in enumerate(nodes):
                input_ = node.inputs[0]
                row = col.row()
                s1_row = row.row()
                s1_row.prop(input_, "show_expanded", icon_only=True, emboss=False,
                            icon='DISCLOSURE_TRI_DOWN' if input_.show_expanded else 'DISCLOSURE_TRI_RIGHT')
                s1_row.active = not node.mute
                s1_row.label(text=node.name)
                s2_row = row.row()
                s2_row.alignment = 'RIGHT'
                s2_row.prop(node, "mute", icon_only=True, emboss=False,
                            icon='CHECKBOX_HLT' if not node.mute else 'CHECKBOX_DEHLT')

                if not input_.show_expanded:
                    continue

                col.separator(factor=0.01)

                row = col.row()
                row.enabled = not node.mute
                row.label(icon='BLANK1')
                row = row.row()
                split = row.split(factor=0.3)
                col1 = split.column()
                col2 = split.column()

                for i in node.inputs:
                    c1_row = col1.row()
                    c1_row.alignment = 'RIGHT'
                    c1_row.label(text=i.name)
                    c2_row = col2.row()
                    s1_row = c2_row.row()
                    s1_row.prop(i, "default_value", text="")

                    if i.is_linked:
                        c1_row.enabled = s1_row.enabled = False
                        s2_row = c2_row.row()
                        op = s2_row.operator("utils.properties_toggle_description", emboss=False, icon='DECORATE_LINKED')
                        op.description = "Linked"

                col.separator(factor=0.25 if (index != len_ - 1) else 0.5)


class MXD_Node_ImageLayers_Controller(Node):
    bl_label = "Layers Controller"
    bl_icon = 'NODETREE'
    bl_width_default = 330

    properties: PointerProperty(type=ImageLayers_Controller)

    def draw_buttons_ext(self, context, layout):
        if not self.id_data.nodes.get(self.properties.target_node_group):
            layout.alert = True
        layout.prop(self.properties, "target_node_group", text="")

    def draw_buttons(self, context, layout):
        col = layout.column()
        SPACE = 0.75
        col.separator(factor=SPACE)
        Base_DrawButtons.invoke(context, col, self.properties, controller=self)
        col.separator(factor=SPACE)


class Base_ImageLayersPanel(Panel):
    @classmethod
    def poll(cls, context):
        return (context.mode == 'PAINT_TEXTURE')

    def draw(self, context):
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        panel = pref.image_layers_panel
        mat = context.object.active_material
        mat_image_layers = mat.image_layers
        target_node_group = mat_image_layers.target_node_group

        layout = self.layout

        if not self.docked:
            layout.ui_units_x = panel.ui_units_x
            row = layout.row()
            s1_row = row.row()
            s1_row.alignment = 'LEFT'
            s1_row.prop(panel, "show_ui_units_x", icon='ARROW_LEFTRIGHT',
                        icon_only=True, emboss=False)
            if panel.show_ui_units_x:
                s1_row.prop(panel, "ui_units_x", text="")

            s2_row = row.row()
            s2_row.alignment = 'RIGHT'
            s2_row.operator("image_layers_panel.info", icon='INFO', emboss=False)

        node = mat.node_tree.nodes.get(target_node_group)
        label = node.node_tree.name if node else target_node_group

        col = layout.column()
        row = col.row()
        row.prop(panel, "is_target_node_group_expanded", icon_only=True, emboss=False,
                 icon='DOWNARROW_HLT' if panel.is_target_node_group_expanded else 'RIGHTARROW')
        row.label(text=f"{mat.name} [{label}]")

        if panel.is_target_node_group_expanded:
            col.separator(factor=0.01)
            row = col.row()
            if not node:
                row.alert = True
            row.label(icon='BLANK1')
            row.prop(mat_image_layers, "target_node_group", text="")
            col.separator(factor=0.75)
        if node:
            Base_DrawButtons.invoke(context, col, mat_image_layers)


class MXD_PT_PaintTexture_ImageLayersPanel(Base_ImageLayersPanel, Panel):
    bl_label = ""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    docked = False


class MXD_MT_Menu_ImageLayers(Menu):
    bl_label = ""

    def draw(self, context):
        global node_group, image_layers
        # If there are multiple controllers, the global variables above will be from the active one
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        panel = pref.image_layers_panel

        layout = self.layout

        if (img_tex := image_layers.get_layer_node('IMG_TEX')) and img_tex.image:
            op = layout.operator("image_layers.add_next_node", text="Add HSV Node")
            op.type = 'ShaderNodeHueSaturation'
            op.node_group = node_group.name
            op.image_texture_node = img_tex.name
            layout.separator()

        layout.prop(context.object.active_material.image_layers, "is_preview_shown")
        layout.separator()
        layout.prop(panel, "show_layer_id")
        layout.prop(panel, "save_images_on_file_save")


classes = (
    MXD_UL_Materials_ImageLayers,
    MXD_Node_ImageLayers_PropStorage,
    MXD_Node_ImageLayers_Controller,
    MXD_PT_PaintTexture_ImageLayersPanel,
    MXD_MT_Menu_ImageLayers,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)