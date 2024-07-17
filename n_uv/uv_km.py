import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='UV Editor')

        kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_UVEditor"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'E', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_UVEditor_MarkEgde"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'R', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_UVEditor_Rotate_Flip"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('uv.select_linked_pick', 'LEFTMOUSE', 'PRESS', key_modifier='W')
        kmi.properties.extend = True
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('uv.move_with_collision', 'G', 'PRESS', key_modifier='W')
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('uv.uv_squares_wrapper', 'E', 'PRESS')
        addon_keymaps.append((km, kmi))
