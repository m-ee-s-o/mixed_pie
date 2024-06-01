import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Property Editor", space_type="PROPERTIES")

        kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
        kmi.properties.name = "MXD_MT_Menu_Material_Preset"
        addon_keymaps.append((km, kmi))
