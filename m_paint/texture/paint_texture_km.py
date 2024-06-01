import bpy
from ...f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Image Paint')

        kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_PaintTexture"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'F', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_PaintTexture_BrushFalloff"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS')
        kmi.properties.name = "MXD_MT_PIE_PaintTexture_Toolbar"
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu_pie', 'E', 'PRESS')
        kmi.properties.name = "MXD_MT_PIE_BrushStrokeMethod"
        addon_keymaps.append((km, kmi))
