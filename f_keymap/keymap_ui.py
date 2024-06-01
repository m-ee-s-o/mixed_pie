import bpy
from bpy.types import Panel
from . import keymap_out


MODES = {
    'OBJECT': {'name': "Object", 'km': "Object Mode"},
    'EDIT_MESH': {'name': "Edit: Mesh", 'km': "Mesh"},
    'EDIT_CURVE': {'name': "Edit: Curve", 'km': "Curve"},
    'EDIT_ARMATURE': {'name': "Edit: Armature", 'km': "Armature"},
    'POSE': {'name': "Pose: Armature", 'km': "Pose"},
    'SCULPT': {'name': "Sculpt", 'km': "Sculpt"},
    'PAINT_TEXTURE': {'name': "Paint: Texture", 'km': "Image Paint"},
    'PAINT_WEIGHT': {'name': "Paint: Weight", 'km': "Weight Paint"},
}


# modified; from Blender, rna_keymap_ui.py
def draw_kmi(col, kmi, add_to_text=""):
    # .addon (can't change) to .user
    # https://blenderartists.org/t/i-have-a-problem-with-my-keymaps/1152252/2
    km = bpy.context.window_manager.keyconfigs.user.keymaps[kmi.km.name]

    if kmi.id_user == 0:
        for item in km.keymap_items:
            if item.name == kmi.name:
                kmi.id_user = item.id
                break
    id = kmi.id_user
    text = kmi.display_name + add_to_text

    kmi = km.keymap_items.from_id(id)
    if not kmi:
        return

    map_type = kmi.map_type

    box = col.column()
    split = box.split()

    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)
    row.label(text=text)

    row = split.row()
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    if (not kmi.is_user_defined) and kmi.is_user_modified:
        row.context_pointer_set("keymap", km)
        row.operator("preferences.keyitem_restore", text="", icon='BACK').item_id = kmi.id
    else:
        row.label(icon='BLANK1')

    if kmi.show_expanded:
        col.separator()
        row = col.row()
        row.separator(factor=2.75)
        box = row.box()
        row.label(icon='BLANK1')
        split = box.split(factor=0.4)
        sub = split.row()
        sub.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row()

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)
            subrow.prop(kmi, "key_modifier", text="", event=True)

        box.template_keymap_item_properties(kmi)
        col.separator()


class MXD_PT_Keymap(Panel):
    bl_label = "Available Keymap in Current Mode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 30

    def draw(self, context):
        km_s = keymap_out.km_s
        ui_type = context.area.ui_type
        c_mode = context.mode

        layout = self.layout
        row = layout.row()
        row.label(text="Keymap")

        box = layout.box()
        row = box.row()
        row.label(text="[Window]")
        col = box.column(align=True)

        for kmi in km_s['Window']:
            draw_kmi(col, kmi)
            col.separator()

        if not (ui_type in {'VIEW_3D', 'UV', 'PROPERTIES'} or ui_type.endswith('NodeTree')):
            return

        box = layout.box()
        row = box.row()
        col = box.column(align=True)

        match ui_type:
            case 'VIEW_3D':
                if c_mode in MODES:
                    mode = MODES[c_mode]
                    row.label(text=f"[3D View] {mode['name']}")
                    for kmi in km_s[mode['km']]:
                        if not kmi.name.startswith((mode['name'], 'Edit', 'Paint', 'Pose')):
                            col.separator()
                        draw_kmi(col, kmi)

                    for kmi in km_s['3D View']:
                        if (c_mode != 'PAINT_TEXTURE'
                                and context.object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}
                                and kmi.name.startswith(("Modifier", "Symmetrize"))):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif (c_mode in {'OBJECT', 'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE',
                                         'EDIT_ARMATURE', 'EDIT_LATTICE', 'POSE'}
                                and kmi.name.startswith(("Scale, 3D View"))):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif (c_mode not in {'OBJECT', 'EDIT_MESH', 'SCULPT'}
                                and kmi.name.startswith("Rotate V")):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif kmi.name.startswith("Align V"):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif (c_mode not in {'EDIT_MESH', 'EDIT_CURVE', 'PAINT_WEIGHT', 'SCULPT'}
                                and kmi.name.startswith("Viewport")):
                            col.separator()
                            draw_kmi(col, kmi)

            case 'UV':
                row.label(text=f"[UV Editor] {MODES[c_mode]['name']}")
                if c_mode == 'EDIT_MESH':
                    first, last = [], []  # Rearrange
                    for kmi in km_s['UV Editor']:
                        if kmi.name.startswith("UV Editor"):
                            first.append(kmi)
                        else:
                            last.append(kmi)
                    for kmi in first:
                        draw_kmi(col, kmi)
                    for kmi in last:
                        col.separator()
                        draw_kmi(col, kmi)
                else:
                    row = col.row()
                    row.alert = True
                    row.label(text="Mode must be Edit: Mesh.")

            case 'PROPERTIES':
                for area in context.screen.areas:
                    if area.type == 'PROPERTIES':
                        active_tab = area.spaces[0].context
                row.label(text=f"[Properties] {active_tab.title().replace('_', ' ')}")
                if active_tab == 'MATERIAL':
                    for kmi in km_s['Property Editor']:
                        draw_kmi(col, kmi)
                else:
                    row = col.row()
                    row.alert = True
                    row.label(text="Active tab must be Material Properties.")

            case _ if ui_type.endswith('NodeTree'):
                row.label(text="[Node Editor]")
                for kmi in km_s['Node Editor']:
                    if not kmi.name.startswith("Node"):
                        col.separator()
                    draw_kmi(col, kmi)

        col.separator()


class Preferences_Keymap:
    @classmethod
    def draw(cls, pref):
        km_s = keymap_out.km_s

        layout = pref.layout
        row = layout.row()
        row.prop(pref.keymap, "changes_expanded", icon_only=True, emboss=False,
                 icon='DISCLOSURE_TRI_DOWN' if pref.keymap.changes_expanded else 'DISCLOSURE_TRI_RIGHT')
        s_row = row.row()
        s_row.enabled = not pref.keymap.set_changes
        s_row.operator("keymap.set_changes", text="— Set Keymap Changes —").mode = "CHANGE"
        row.operator("keymap.set_changes", icon='FILE_REFRESH', emboss=False).mode = "REVERT"

        if pref.keymap.changes_expanded:
            col_m = layout.column()
            if pref.keymap.kmi_changes:
                for kmi in pref.keymap.kmi_changes:
                    box = col_m.box()
                    box.label(text=kmi.km_name)
                    col = box.column(align=True)
                    draw_kmi(col, km_name=kmi.km_name, id=kmi.kmi_id)
            else:
                box = col_m.box()
                row = box.row()
                row.alignment = 'CENTER'
                row.label(text="Unset" if not pref.keymap.set_changes else "Already Suitable | Nothing to show")

        col_m = layout.column()
        row = col_m.row()
        row.prop(pref.keymap, "expanded", icon_only=True, emboss=False,
                    icon='DISCLOSURE_TRI_DOWN' if pref.keymap.expanded else 'DISCLOSURE_TRI_RIGHT')
        row.label(text="Keymap")

        if pref.keymap.expanded:
            group_by_mode = pref.keymap.group_relation_or_mode
            row.prop(pref.keymap, "group_relation_or_mode", icon_only=True, emboss=False,
                        icon='EVENT_M' if group_by_mode else 'EVENT_R')
            col_m.separator(factor=0.5)

            if group_by_mode:
                uv_editor = []
                first, last = [], []  # Rearrange
                for kmi in km_s['UV Editor']:
                    if kmi.name.startswith("UV Editor"):
                        first.append(kmi)
                    else:
                        last.append(kmi)
                uv_editor.append(first)
                uv_editor.extend([[kmi] for kmi in last])

                cls.draw_group(col_m, "[Window]", [[kmi] for kmi in km_s['Window']])
                cls.draw_group(col_m, "[3D View]", [[kmi] for kmi in km_s['3D View']])

                for mode in MODES:
                    box = col_m.box()
                    box.label(text=f"[3D View] {MODES[mode]['name']}")
                    col = box.column(align=True)
                    for kmi in km_s[MODES[mode]['km']]:
                        if not kmi.name.startswith((MODES[mode]['name'], 'Edit', 'Paint', 'Pose')):
                            col.separator()
                        draw_kmi(col, kmi)

                    for kmi in km_s['3D View']:
                        if (mode not in {'EDIT_ARMATURE', 'POSE', 'PAINT_TEXTURE'}
                                and kmi.name.startswith(("Modifier", "Symmetrize"))):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif (mode not in {'OBJECT', 'EDIT_MESH', 'SCULPT'}
                                and kmi.name.startswith("Rotate V")):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif kmi.name.startswith("Align V"):
                            col.separator()
                            draw_kmi(col, kmi)
                        elif (mode not in {'EDIT_MESH', 'EDIT_CURVE', 'PAINT_WEIGHT', 'SCULPT'}
                                and kmi.name.startswith("Viewport")):
                            col.separator()
                            draw_kmi(col, kmi)

                cls.draw_group(col_m, "[UV Editor] Edit: Mesh", uv_editor)
                cls.draw_group(col_m, "[Node Editor]", [[kmi] for kmi in km_s['Node Editor']])
                cls.draw_group(col_m, "[Properties] Material", [km_s['Property Editor']])

            else:
                align_view, rotate_view, viewport_display, scale, modifier = [], [], [], [], []
                for kmi in km_s['3D View']:
                    match kmi.name:
                        case "Viewport Display":
                            viewport_display.append(kmi)
                        case "Align View to Active":
                            align_view.append(kmi)
                        case "Rotate View":
                            rotate_view.append(kmi)
                        case "Symmetrize" | "Modifier":
                            modifier.append(kmi)
                        case _:
                            raise NotImplementedError

                cls.draw_group(col_m, "[Window]", [[kmi] for kmi in km_s['Window']])

                modes_scale = []
                for mode in MODES:
                    mode = MODES[mode]
                    include = []
                    for kmi in km_s[mode['km']]:
                        match kmi.name:
                            case "Rotate View":
                                rotate_view.append(kmi)
                            case "Viewport Display":
                                viewport_display.append(kmi)
                            case _ as e if e.startswith("Scale"):
                                modes_scale.append(kmi)
                            case _:
                                include.append(kmi)

                    cls.draw_group(col_m, f"{mode['name']}", [include])
                scale.append(modes_scale)

                uv_editor, uv_editor_others = [], []
                for kmi in km_s['UV Editor']:
                    if kmi.name.startswith("Scale"):
                        scale.append([kmi])
                    elif kmi.name.startswith("UV Editor"):
                        uv_editor.append(kmi)
                    else:
                        uv_editor_others.append(kmi)

                node_editor = []
                for kmi in km_s['Node Editor']:
                    if kmi.name.startswith("Scale"):
                        scale.append([kmi])
                    else:
                        node_editor.append(kmi)

                cls.draw_group(col_m, "UV Editor", [uv_editor, *[[kmi] for kmi in uv_editor_others]])
                cls.draw_group(col_m, "ScaleXYZby", scale)
                cls.draw_group(col_m, "Modifier", [[kmi] for kmi in modifier])
                cls.draw_group(col_m, "Material Properties", [[kmi for kmi in km_s['Property Editor'] if kmi.name.startswith("Material")]])
                cls.draw_group(col_m, "Node Editor", [node_editor])
                cls.draw_group(col_m, "View 3D", [align_view, rotate_view, viewport_display])

    @classmethod
    def draw_group(cls, col_m, text, lst_of_lst):
        box = col_m.box()
        box.label(text=text)
        col = box.column(align=True)
        for lst in lst_of_lst:
            for kmi in lst:
                draw_kmi(col, kmi)
            col.separator()


classes = (
    MXD_PT_Keymap,
)


def register():
    global _change_value
    _change_value = False

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
