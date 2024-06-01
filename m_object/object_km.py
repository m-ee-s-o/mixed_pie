import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode')

        kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_Object"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS', key_modifier='D')
        kmi.properties.name = "MXD_MT_PIE_Object_ClearTransform"
        addon_keymaps.append((km, kmi))
