import bpy
from ...f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_Node"
        addon_keymaps.append((km, kmi))
