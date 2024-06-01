import bpy
from bpy.types import PropertyGroup
from bl_operators.node import NodeSetting


class AddNode_NodeSetting_Set(NodeSetting, PropertyGroup):
    def set(self, name, value):
        self.name = name
        self.value = value


class AddNode_NodeSetting_EventOverwrite(PropertyGroup):
    @property
    def value(self):
        return self.get('_overwrite')

    @value.setter
    def value(self, value):
        self['_overwrite'] = value


classes = (
    AddNode_NodeSetting_Set,
    AddNode_NodeSetting_EventOverwrite,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
