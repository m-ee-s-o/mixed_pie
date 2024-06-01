import bpy
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty, StringProperty


class MXD_CollT_Bone_Parent(PropertyGroup):
    name: StringProperty()
    parent: StringProperty()

    def set(self, name, parent):
        self.name = name
        self.parent = parent


class MXD_Pref_Armature(PropertyGroup):
    bones_parents: CollectionProperty(type=MXD_CollT_Bone_Parent)
    active_BoneParent: IntProperty()


classes = (
    MXD_CollT_Bone_Parent,
    MXD_Pref_Armature,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
