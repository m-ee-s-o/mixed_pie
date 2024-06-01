import bpy


addon_keymaps = []


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km1 = kc.keymaps.new(name='Window')

        kmi = km1.keymap_items.new('wm.call_panel', 'F1', 'PRESS', key_modifier='W')
        kmi.properties.name = "MXD_PT_Keymap"
        addon_keymaps.append((km1, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
