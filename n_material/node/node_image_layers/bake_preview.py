import bpy
from ..node_utils import get_node_space


class BakePreview:
    node_group = None

    def revert_bake_preview(self):
        node_groups = bpy.data.node_groups
        nodes = bpy.context.object.active_material.node_tree.nodes
        if (node := nodes.get("DoNotChange_BakePreview")):
            if (node_group := node_groups.get(self.preview_type)):
                if node_group.users == 1:
                    node_groups.remove(node_group)
            nodes.remove(node)
        if (node := nodes.get("DoNotChange_BakeMaterialOutput")):
            nodes.remove(node)

    def get_bake_preview(self):
        nodes = bpy.context.object.active_material.node_tree.nodes
        if self.node_group and self.node_group.node_tree:
            if (node := nodes.get("DoNotChange_BakePreview"))  \
                    and (node_tree := node.node_tree)          \
                    and node_tree.name == self.preview_type:
                if (node := nodes.get("DoNotChange_BakeMaterialOutput")) and node.is_active_output:
                    return True

        self.revert_bake_preview()
        return False

    def make_bake_preview(self, type):
        node_groups = bpy.data.node_groups
        X_SPACE, _ = get_node_space()
        match type:
            case "Preview w/ Alpha" as name:
                preview = node_groups.new(name, 'ShaderNodeTree')
                interface = preview.interface
                nodes = preview.nodes
                links = preview.links

                interface.new_socket(name="Color", in_out='INPUT', socket_type='NodeSocketColor')
                interface.new_socket(name="Alpha", in_out='INPUT', socket_type='NodeSocketColor')
                interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')

                group_input = nodes.new(type='NodeGroupInput')

                reverse_alpha_mul = nodes.new(type='ShaderNodeMix')
                reverse_alpha_mul.data_type = 'RGBA'
                reverse_alpha_mul.blend_type = 'DIVIDE'
                reverse_alpha_mul.inputs['Factor'].default_value = 1
                reverse_alpha_mul.location.x = group_input.width + X_SPACE
                reverse_alpha_mul.location.y = 152

                transparent_bdsf = nodes.new(type='ShaderNodeBsdfTransparent')
                transparent_bdsf.location.x = reverse_alpha_mul.location.x + reverse_alpha_mul.width + X_SPACE
                transparent_bdsf.location.y -= 44

                mix_shader = nodes.new(type='ShaderNodeMixShader')
                mix_shader.location.x = transparent_bdsf.location.x + transparent_bdsf.width + X_SPACE
                mix_shader.location.y = 3

                group_output = nodes.new(type='NodeGroupOutput')
                group_output.location = mix_shader.location
                group_output.location.x += mix_shader.width + X_SPACE

                links.new(group_input.outputs['Color'], reverse_alpha_mul.inputs[6])
                links.new(group_input.outputs['Alpha'], reverse_alpha_mul.inputs[7])
                links.new(group_input.outputs['Alpha'], mix_shader.inputs['Fac'])
                links.new(reverse_alpha_mul.outputs[2], mix_shader.inputs[2])
                links.new(transparent_bdsf.outputs['BSDF'], mix_shader.inputs[1])
                links.new(mix_shader.outputs['Shader'], group_output.inputs['Shader'])

            case "Preview w/o Alpha" as name:
                preview = node_groups.new(name, 'ShaderNodeTree')
                nodes = preview.nodes
                links = preview.links

                interface.new_socket(name="Color", in_out='INPUT', socket_type='NodeSocketColor')
                interface.new_socket(name="Alpha", in_out='INPUT', socket_type='NodeSocketColor')
                interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')

                group_input = nodes.new(type='NodeGroupInput')

                group_output = nodes.new(type='NodeGroupOutput')
                group_output.location.x = group_input.width + X_SPACE

                links.new(group_input.outputs['Color'], group_output.inputs['Color'])

        for node in nodes:
            node.select = False
        return preview

    def set_bake_preview(self, value):
        if value:
            node_tree = bpy.context.object.active_material.node_tree
            nodes = node_tree.nodes

            mat_output = nodes.new(type='ShaderNodeOutputMaterial')
            mat_output.name = "DoNotChange_BakeMaterialOutput"
            mat_output.select = False
            mat_output.is_active_output = True

            bake_preview = nodes.new(type='ShaderNodeGroup')
            bake_preview.name = "DoNotChange_BakePreview"
            bake_preview.select = False
            bake_preview.label = "Bake Preview"
            if not (bake_preview_group := bpy.data.node_groups.get(self.preview_type)):
                bake_preview_group = self.make_bake_preview(self.preview_type)
            bake_preview.node_tree = bake_preview_group

            if (node_group := self.node_group):
                frame = node_group.parent
                node_group.parent = None

                X_SPACE, _ = get_node_space()
                bake_preview.width = node_group.width
                bake_preview.location.x = node_group.location.x + node_group.width + X_SPACE
                bake_preview.location.y = node_group.location.y + 55

                node_group.parent = frame

                mat_output.location.x = bake_preview.location.x + bake_preview.width + X_SPACE
                mat_output.location.y = bake_preview.location.y + 25

                links = node_tree.links
                links.new(node_group.outputs['Color'], bake_preview.inputs['Color'])
                links.new(node_group.outputs['Alpha'], bake_preview.inputs['Alpha'])
                links.new(bake_preview.outputs[0], mat_output.inputs['Surface'])
        else:
            self.revert_bake_preview()
