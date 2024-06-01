import bpy
from bpy.types import Menu


EXEC_RENAME_CONTROLLER = """
node.name = "LayersController"
parts = node.name.rpartition(".")
node.label = "Layers Controller" + (f" {parts[-1]}" if all(parts) else "")
"""


EXEC_IMAGE_LAYERS = f"""
mat = context.object.active_material
from .node_utils import get_node_space
FRAME_X_MARGIN, FRAME_Y_MARGIN = get_node_space()

bpy.ops.node.add('INVOKE_DEFAULT', type='ShaderNodeGroup', use_transform=False, store_node=True)
ng = eval(mat['tmp_node'])
NG_HEIGHT = 102

bpy.ops.node.add('INVOKE_DEFAULT', type='NodeFrame', use_transform=False, store_node=True)
frame = eval(mat['tmp_node'])
del mat['tmp_node']

{EXEC_RENAME_CONTROLLER}
node.properties.set_target_node_group_string(f'{"{ng.name}"}')
node.location.x += FRAME_X_MARGIN
node.location.y -= NG_HEIGHT + (FRAME_Y_MARGIN / 3) + FRAME_Y_MARGIN

ng.width *= 1.5
ng.location.x += node.width - ng.width + FRAME_X_MARGIN
ng.location.y -= FRAME_Y_MARGIN

node.select = ng.select =True
node.parent = ng.parent = frame
"""


EXEC_MIX_NODE_GROUP = """
from .node_image_layers.image_layers_op import make_mix_group

mix_group = make_mix_group()
node.node_tree = mix_group
node.width *= 1.5
"""


class MXD_MT_PIE_Node(Menu):
    bl_label = "Node"

    def draw(self, context):
        # for input in context.active_node.inputs:
        #     print(input)

        # print(context.active_node.dimensions)
        # print(context.preferences.system.dpi)
        # print(get_node_space())
        # print(context.active_node)

        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left

        op = pie.operator("node.add", text="Multiply RGBA", icon='BLANK1')         # Right
        op.type = 'ShaderNodeMix'
        op.settings.add().set("data_type", "'RGBA'")
        op.settings.add().set("blend_type", "'MULTIPLY'")

        pie.separator()  # Bottom
        pie.separator()  # Top

        op = pie.operator("node.add", text="Image Layers", icon='BLANK1')         # Top_left
        op.description = "Add an image layers setup.\n\n"     \
                         "Alt: Add only layer controller.\n"  \
                         "Ctrl: Add only node group.\n"       \
                         'Shift: Add only "MixGroup"'
        op.type = "MXD_Node_ImageLayers_Controller"
        op.exec = EXEC_IMAGE_LAYERS
        op.event_overwrite.value = {
            'alt': f'self.exec = """{EXEC_RENAME_CONTROLLER}"""',
            'ctrl': "self.type = 'ShaderNodeGroup'; self.exec = ''",
            'shift': f'self.type = "ShaderNodeGroup"; self.exec = """{EXEC_MIX_NODE_GROUP}"""',
        }

        op = pie.operator("node.add", text="Mix RGBA", icon='BLANK1')              # Top_right
        op.type = 'ShaderNodeMix'
        op.settings.add().set("data_type", "'RGBA'")

        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_Node,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
