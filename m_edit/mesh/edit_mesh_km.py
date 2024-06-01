import bpy
from ...f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh')

        kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_EditMesh"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_EditMesh_Select"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'E', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_EditMesh_MarkEgde"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'F', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_LoopTools"
        addon_keymaps.append((km, kmi))
