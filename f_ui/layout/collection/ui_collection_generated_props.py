import bpy
from bpy.props import PointerProperty
from .ui_collection_prop import MXD_UICollection_PointT_UI_Collection


register_template = "    bpy.types.<id_data_identifier>.<properties_attr> = PointerProperty(type=MXD_UICollection_PointT_UI_Collection)\n"
unregister_template = "    del bpy.types.<id_data_identifier>.<properties_attr>\n"


def register():
    bpy.types.Armature.MixedPie_UICollection_BoneCollections = PointerProperty(type=MXD_UICollection_PointT_UI_Collection)
    pass


def unregister():
    del bpy.types.Armature.MixedPie_UICollection_BoneCollections
    pass
