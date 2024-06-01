import bpy


def get_node_space():
    DEV_DPI = 144
    DEV_SPACE = 30
    return (DEV_DPI / bpy.context.preferences.system.dpi * DEV_SPACE, DEV_SPACE)
