import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km_a = kc.keymaps.new(name="Armature")
        km_p = kc.keymaps.new(name="Pose")

        for km in [km_a, km_p]:
            kmi = km.keymap_items.new('wm.call_menu_pie', 'D', 'PRESS', key_modifier='W')
            kmi.properties.name = "MXD_MT_PIE_Armature"
            addon_keymaps.append((km, kmi))

            kmi = km.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS', key_modifier='W')
            kmi.properties.name = "MXD_MT_PIE_Armature_SetAndForget"
            addon_keymaps.append((km, kmi))

        kmi = km_p.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS', key_modifier='D')
        kmi.properties.name = "MXD_MT_PIE_Pose_ClearTranform"
        addon_keymaps.append((km_p, kmi))
