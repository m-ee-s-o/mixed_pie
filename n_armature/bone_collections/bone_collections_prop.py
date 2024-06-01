import bpy
from bpy.types import BoneCollection, PropertyGroup
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty


class MXD_CollT_PathToBoneCollection(PropertyGroup):
    obj_name: StringProperty()
    coll_name: StringProperty()
    include: BoolProperty(name="", default=True)

    def set(self, obj_name, coll_name):
        self.obj_name = obj_name
        self.coll_name = coll_name


class MXD_PointT_BoneCollections(PropertyGroup):
    locked: BoolProperty()


class MXD_CollT_ItemForColumn(PropertyGroup):
    include: BoolProperty(name="")
    generation: IntProperty()
    bone_collection: StringProperty()


class MXD_Pref_UI_BoneCollections(PropertyGroup):
    show_lock: BoolProperty(name="Show Lock", default=True)
    show_solo: BoolProperty(name="Show Solo")
    is_expanded: BoolProperty(name="", default=True)


classes = (
    MXD_PointT_BoneCollections,
    MXD_CollT_PathToBoneCollection,
    MXD_CollT_ItemForColumn,
    MXD_Pref_UI_BoneCollections,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    BoneCollection.MixedPie = PointerProperty(type=MXD_PointT_BoneCollections)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del BoneCollection.MixedPie