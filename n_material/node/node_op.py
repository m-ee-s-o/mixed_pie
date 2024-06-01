import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, CollectionProperty, PointerProperty, StringProperty
from bl_operators.node import NODE_OT_add_node, NodeAddOperator
from .node_prop import AddNode_NodeSetting_Set, AddNode_NodeSetting_EventOverwrite


class MXD_OT_Node_Add(NodeAddOperator, Operator):
    bl_idname = "node.add"
    bl_label = "Add Node"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    type: StringProperty()
    use_transform: BoolProperty(default=True, options={'SKIP_SAVE'})
    settings: CollectionProperty(type=AddNode_NodeSetting_Set, options={'SKIP_SAVE'})
    description: StringProperty(options={'SKIP_SAVE'}, default="")
    event_overwrite: PointerProperty(type=AddNode_NodeSetting_EventOverwrite, options={'SKIP_SAVE'})
    exec: StringProperty(options={'SKIP_SAVE'})
    store_node: BoolProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return NODE_OT_add_node.description(context, properties) + properties.description

    def execute(self, context):
        if self.properties.is_property_set("type"):
            self.deselect_nodes(context)
            node = self.create_node(context, self.type)
            if self.exec:
                exec(self.exec)          
            if self.store_node:
                context.object.active_material['tmp_node'] = repr(node)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def invoke(self, context, event):
        if (event_overwrite := self.event_overwrite.value):
            for event_, overwrite in event_overwrite.items():
                if getattr(event, event_):
                    if not isinstance(overwrite, str):
                        for name, value in overwrite:
                            for setting in self.settings:
                                if setting.name == name:
                                    setting.value = value
                                    break
                            else:
                                self.settings.add().set(name, value)
                    else:
                        exec(overwrite)
        return super().invoke(context, event)


classes = ( 
    MXD_OT_Node_Add,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
