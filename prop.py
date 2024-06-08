import bpy
from bpy.types import AddonPreferences
from bpy.props import PointerProperty

from .f_keymap.keymap_prop import Keymap
from .f_keymap.keymap_ui import Preferences_Keymap

from .n_armature.bone_collections.bone_collections_prop import MXD_Pref_UI_BoneCollections
from .n_armature.armature_prop import MXD_Pref_Armature

from .n_material.node.node_image_layers.image_layers_prop import ImageLayers_Panel

from .f_ui.layout.collection.ui_collection_prop import MXD_Pref_UICollection_List


class AddonPreferences(AddonPreferences):
    bl_idname = __package__

    keymap: PointerProperty(type=Keymap)
    ui_collections: PointerProperty(type=MXD_Pref_UICollection_List)
    ui_bone_collections: PointerProperty(type=MXD_Pref_UI_BoneCollections)
    image_layers_panel: PointerProperty(type=ImageLayers_Panel)
    armature: PointerProperty(type=MXD_Pref_Armature)

    def draw(self, context):
        Preferences_Keymap.draw(pref=self)


classes = (
    AddonPreferences,    
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
