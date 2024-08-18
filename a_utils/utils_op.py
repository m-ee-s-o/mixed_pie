import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty


class MXD_OT_Utils_TogglePropertiesButWithDesciption(Operator):
    bl_idname = "utils.properties_toggle_description"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    parent: StringProperty(options={'SKIP_SAVE'})
    prop: StringProperty(options={'SKIP_SAVE'})
    # slider_ends: StringProperty(options={'SKIP_SAVE'})
    description: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return properties.description

    def execute(self, context):
        if not self.parent:
            return {'CANCELLED'}

        parent = eval(self.parent)
        # elif self.slider_ends:
        #     a, b = self.slider_ends.split('-')
        #     a, b = int(a), int(b)
        #     setattr(parent, self.prop, a if getattr(parent, self.prop) == b else b)
        if self.prop:
            setattr(parent, self.prop, not getattr(parent, self.prop))

        return {'FINISHED'}
    

class MXD_OT_Utils_ModifyCollectionItem(Operator):
    bl_idname = "utils.modify_collection_item"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}    

    operation: StringProperty(options={'SKIP_SAVE'})
    collection: StringProperty(options={'SKIP_SAVE'})
    index: IntProperty(options={'SKIP_SAVE'})
    index_path: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        match properties.operation:
            case 'ADD':
                return ""
            case 'REMOVE':
                return ""

    def execute(self, context):
        collection = eval(self.collection)
        match self.operation:
            case 'ADD':
                collection.add()
                collection.move(len(collection) - 1, self.index)
            case 'REMOVE':
                collection.remove(self.index)
                if self.index > len(collection) - 1:
                    parent, attr = self.index_path.rsplit(".", 1)
                    setattr(eval(parent), attr, len(collection) - 1)
            case 'MOVE_UP' if self.index > 0:
                collection.move(self.index, self.index - 1)
                parent, attr = self.index_path.rsplit(".", 1)
                setattr(eval(parent), attr, self.index - 1)
            case 'MOVE_DOWN' if self.index < len(collection) - 1:
                collection.move(self.index, self.index + 1)
                parent, attr = self.index_path.rsplit(".", 1)
                setattr(eval(parent), attr, self.index + 1)
        return {'FINISHED'}
    

class MXD_OT_Utils_Dummy(Operator):
    bl_idname = "utils.dummy"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        return {'CANCELLED'}


classes = (
    MXD_OT_Utils_TogglePropertiesButWithDesciption,
    MXD_OT_Utils_ModifyCollectionItem,
    MXD_OT_Utils_Dummy,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
