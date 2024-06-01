import bpy
from bpy_types import Operator
from bpy.props import StringProperty


class MXD_OT_SetKeymapChanges(Operator):
    bl_idname = "keymap.set_changes"
    bl_label = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    mode: StringProperty()

    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'CHANGE':
                return "— [3D View, UV Editor] Disable fallback tool cycle keymap (W).\n"  \
                       "— [Sculpt] Change face sets edit pie key binding (W) to Alt+W"
            case 'REVERT':
                return "Revert changes"

    def execute(self, context):
        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        keymap = pref.keymap

        kc = context.window_manager.keyconfigs.user
        km_view_3d = kc.keymaps["3D View"]
        km_uv_editor = kc.keymaps["UV Editor"]
        km_sculpt = kc.keymaps["Sculpt"]
        match self.mode:
            case 'CHANGE':
                keymap.set_changes = True
                # Disable fallback tool cycle key (W) to use W as key modifier
                # Alt+W can still be used to call fallback tool pie
                for km, prior in ((km_view_3d, "view_3d_w_prior_state"),
                                  (km_uv_editor, "uv_editor_w_prior_state")):
                    for kmi in km.keymap_items:
                        if kmi.idname == 'wm.tool_set_by_id':
                            if kmi.properties.name == 'builtin.select_box':
                                if kmi.type == 'W':
                                    if kmi.active:
                                        setattr(keymap, prior, kmi.active)
                                        keymap.kmi_changes.add().set(km.name, kmi.id)
                                        kmi.active = False
                                        break
                # Change face sets edit pie key (W) to alt+W to use W as key modifier
                for kmi in km_sculpt.keymap_items:
                    if kmi.idname == 'wm.call_menu_pie':
                        if kmi.properties.name == 'VIEW3D_MT_sculpt_face_sets_edit_pie':
                            if kmi.type == 'W':
                                if not kmi.alt_ui:
                                    keymap.sculpt_w_prior_state = kmi.alt_ui
                                    keymap.kmi_changes.add().set(km_sculpt.name, kmi.id)
                                    kmi.alt_ui = True
                                break
            case 'REVERT':
                keymap.set_changes = False
                keymap.kmi_changes.clear()
                for km, prior in ((km_view_3d, "view_3d_w_prior_state"),
                                  (km_uv_editor, "uv_editor_w_prior_state")):
                    for kmi in km.keymap_items:
                        if kmi.idname == 'wm.tool_set_by_id':
                            if kmi.properties.name == 'builtin.select_box':
                                kmi.active = getattr(keymap, prior)
                                break
                for kmi in km_sculpt.keymap_items:
                    if kmi.idname == 'wm.call_menu_pie':
                        if kmi.properties.name == 'VIEW3D_MT_sculpt_face_sets_edit_pie':
                            kmi.alt_ui = keymap.sculpt_w_prior_state
                            break
        return {'FINISHED'}


classes = (
    MXD_OT_SetKeymapChanges,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
