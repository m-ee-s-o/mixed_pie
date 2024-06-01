import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window')

        kmi = km.keymap_items.new('wm.call_panel', 'F2', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_PT_Scripts"
        addon_keymaps.append((km, kmi))
