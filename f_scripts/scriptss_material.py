from bpy.types import Context, Operator


class To_BSDF:
    """
    Link a BSDF node to an Output node.
    If there is no BSDF node, search for an Emission node and make a BSDF node based on that. 
    """

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for mat in obj.data.materials:
                if mat.name == "Outline":
                    continue
                node_tree = mat.node_tree
                nodes = node_tree.nodes
                output = node_tree.get_output_node('ALL')
                if not output:
                    continue

                emission = None
                for node in nodes:
                    match node.bl_idname:
                        case 'ShaderNodeBsdfPrincipled':
                            node_tree.links.new(node.outputs['BSDF'], output.inputs['Surface'])
                            break
                        case 'ShaderNodeEmission':
                            emission = node
                else:
                    if not emission:
                        continue
                    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
                    bsdf.location = emission.location
                    bsdf.location.x -= bsdf.width + 30
                    bsdf.inputs['Base Color'].default_value = emission.inputs['Color'].default_value
                    node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])


class To_Emission:
    """
    Link an Emission node to an Output node.
    If there is no Emission node, search for a BSDF node and make an Emission node based on that. 
    """

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for mat in obj.data.materials:
                if mat.name == "Outline":
                    continue
                node_tree = mat.node_tree
                nodes = node_tree.nodes
                output = node_tree.get_output_node('ALL')
                if not output:
                    continue
                bsdf = None
                for node in nodes:
                    match node.bl_idname:
                        case 'ShaderNodeEmission':
                            node_tree.links.new(node.outputs['Emission'], output.inputs['Surface'])
                            break
                        case 'ShaderNodeBsdfPrincipled':
                            bsdf = node
                else:
                    if not bsdf:
                        continue
                    emission = nodes.new('ShaderNodeEmission')
                    emission.location = bsdf.location
                    emission.location.x -= emission.width + 30
                    emission.inputs['Color'].default_value = bsdf.inputs['Base Color'].default_value
                    node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
