import bpy
from .scripts_init import scripts


def Origin_To_Selected(context):
    pre_cursor_location = context.scene.cursor.location.copy()

    bpy.ops.view3d.snap_cursor_to_selected()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.mode_set(mode='EDIT')
    context.scene.cursor.location = pre_cursor_location


funcs = (
    Origin_To_Selected,
)


def register():
    for func in funcs:
        scripts[__name__.split("_")[-1].title()].append(func)
