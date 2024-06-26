import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, StringProperty


class MXD_OT_Material_Preset(Operator):
    bl_idname = "material.preset"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Add material preset"
    bl_space_type = 'PROPERTIES'

    type: StringProperty(options={'SKIP_SAVE'})
    color: FloatVectorProperty(name="Emission Color", subtype='COLOR', size=4, default=(1, 1, 1, 1))

    @classmethod
    def poll(self, context):
        return (obj := context.object) and (obj.type == 'MESH')

    def invoke(self, context, event):
        if self.type == 'EMISSION':
            return context.window_manager.invoke_props_dialog(self, width=400)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.separator(factor=0.5)
        layout.use_property_split = True
        layout.separator()
        layout.separator()
        layout.prop(self, "color")
        layout.separator()
        layout.separator()

    def execute(self, context):
        self.materials = bpy.data.materials
        obj = context.object
        match self.type:
            case 'OUTLINE':
                material = self.outline()
            case 'EMISSION':
                material = self.emissive_plain_color(name="Emission", color=self.color)

        obj_materials = obj.data.materials
        if getattr(self, "check", False):
            if material.name in obj_materials:
                return {'CANCELLED'}

        if getattr(self, "append", True):
            obj_materials.append(material)

        if getattr(self, "set_to_active", False):
            obj.active_material_index = len(obj_materials) - 1
        return {'FINISHED'}

    def new_blank_mat(self, name=None):
        material = self.materials.new(name=(name or "Material"))
        material.use_nodes = True
        material.use_backface_culling = True

        for node in (nodes := material.node_tree.nodes):
            nodes.remove(node)

        return material

    def emissive_plain_color(self, name=None, color=None):
        material = self.new_blank_mat(name)
        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        output = nodes.new('ShaderNodeOutputMaterial')

        emission = nodes.new('ShaderNodeEmission')
        emission.location.x -= output.width + 30
        emission.inputs['Color'].default_value = color or (0, 0, 0, 1)

        links.new(emission.outputs['Emission'], output.inputs['Surface'])

        for node in nodes:
            node.select = False

        self.set_to_active = True
        return material

    def outline(self):
        if not (material := self.materials.get("Outline")):
            material = self.emissive_plain_color(name="Outline")
            material.diffuse_color = (0, 0, 0, 0)  # Color of outline in viewport display, don't show outline

        self.check = True
        self.set_to_active = False
        return material


classes = (
    MXD_OT_Material_Preset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
