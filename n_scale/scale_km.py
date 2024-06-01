import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        key1 = 'S'

        # km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        # kmi = km.keymap_items.new('wm.call_menu_pie', key1, 'PRESS', key_modifier='D')
        # kmi.properties.name = "MXD_MT_PIE_Scale_VP"
        # addon_keymaps.append((km, kmi))

        kms = (kc.keymaps.new(name='Object Mode'),
               kc.keymaps.new(name='Mesh'),
               kc.keymaps.new(name="Armature"),
               kc.keymaps.new(name="Pose"),
               )
        for km in kms:
            kmi = km.keymap_items.new('wm.call_menu_pie', key1, 'PRESS', key_modifier='D')
            kmi.properties.name = "MXD_MT_PIE_Scale_VP"
            addon_keymaps.append((km, kmi))

        km = kc.keymaps.new(name='UV Editor')
        kmi = km.keymap_items.new('wm.call_menu_pie', key1, 'PRESS', key_modifier='D')
        kmi.properties.name = "MXD_MT_PIE_Scale_UVE"
        addon_keymaps.append((km, kmi))

        # kmi = km.keymap_items.new('wm.call_menu_pie', 'A', 'PRESS', key_modifier='D')
        # kmi.properties.name = "MXD_MT_PIE_Scale_UVE_1"
        # addon_keymaps.append((km, kmi))

        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu_pie', key1, 'PRESS', key_modifier='D')
        kmi.properties.name = "MXD_MT_PIE_Scale_NE"
        addon_keymaps.append((km, kmi))
