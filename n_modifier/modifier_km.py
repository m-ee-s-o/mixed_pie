import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

        kmi = km.keymap_items.new('wm.call_menu_pie', 'SEMI_COLON', 'PRESS')
        kmi.properties.name = "MXD_MT_PIE_Modifier"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'QUOTE', 'PRESS')
        kmi.properties.name = "MXD_MT_PIE_Modifier_Symmetrize"
        addon_keymaps.append((km, kmi))
