import bpy
from ..f_keymap.keymap_init import addon_keymaps


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        # Blender 4.0, VIEW_3D keymaps take lesser priority
        # kmi = km_1.keymap_items.new('view3d.rotate_view', 'R', 'PRESS', key_modifier='W')
        # addon_keymaps.append((km_1, kmi))

        kms = (kc.keymaps.new(name='3D View', space_type='VIEW_3D'),
               kc.keymaps.new(name='Object Mode'),
               kc.keymaps.new(name='Mesh'),
               kc.keymaps.new(name='Sculpt'),
               )
        for km in kms:
            kmi = km.keymap_items.new('view3d.rotate_view', 'R', 'PRESS', key_modifier='W')
            addon_keymaps.append((km, kmi))

        km_1 = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        kmi = km_1.keymap_items.new('wm.call_menu_pie', 'ACCENT_GRAVE', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_MT_PIE_AlignViewToActive"
        addon_keymaps.append((km_1, kmi))

        kms = (km_1,
               kc.keymaps.new(name='Mesh'),
               kc.keymaps.new(name='Sculpt'),
               kc.keymaps.new(name='Curve'),
               kc.keymaps.new(name='Weight Paint'),
               )
        for km in kms:
            kmi = km.keymap_items.new('wm.call_menu_pie', 'V', 'PRESS', key_modifier='D')
            kmi.properties.name = "MXD_MT_PIE_ViewportDisplay"
            addon_keymaps.append((km, kmi))
