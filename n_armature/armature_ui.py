import bpy
from bpy.types import UIList, UI_UL_list, Menu, Panel
import addon_utils


class MXD_MT_PIE_Armature(Menu):
    bl_label = "Edit: Armature"

    def draw(self, context):
        tool_settings = context.scene.tool_settings
        snap = tool_settings.use_snap
        proportional_editing = tool_settings.use_proportional_edit
        not_weight_paint = (context.mode != 'PAINT_WEIGHT')
        obj = context.object
        data = obj.data
        if not_weight_paint:
            position = data.pose_position

        layout = self.layout
        pie = layout.menu_pie()
        pie.enabled = (context.mode in {'EDIT_ARMATURE', 'POSE', 'PAINT_WEIGHT'})

        pie.operator("bone_collections.show_all", icon='BONE_DATA')                                           # Left

        match context.mode:
            case 'EDIT_ARMATURE':
                use_mirror = data.use_mirror_x
                pie.operator("wm.context_toggle", depress=(use_mirror),
                             icon='CHECKBOX_HLT' if use_mirror else 'CHECKBOX_DEHLT',
                             text="X-Axis Mirror").data_path = "object.data.use_mirror_x"
            case 'POSE':
                use_mirror = obj.pose.use_mirror_x
                pie.operator("wm.context_toggle", depress=(use_mirror),
                             icon='CHECKBOX_HLT' if use_mirror else 'CHECKBOX_DEHLT',
                             text="X-Axis Mirror").data_path = "object.pose.use_mirror_x"
            case _:
                pie.separator()  # Right

        pie.operator("bone_collections.hide", icon='BONE_DATA',                                          # Bottom
                     text="Hide All Collections Except Selected").mode = 'EXCEPT_SELECTED'

        if not_weight_paint:
            pie.operator("mode.use_snap", depress=(snap),
                         icon='CHECKBOX_HLT' if snap else 'CHECKBOX_DEHLT')
        else:
            pie.separator()  # Top

        pie.operator("bone_collections_panel.invoke", icon='BONE_DATA')
        # pie.operator("wm.call_panel", icon='BONE_DATA',                                               # Top_left
        #              text="Bone Layers").name = "MXD_PT_Armature_BoneCollectionsPanel"

        if context.mode == 'EDIT_ARMATURE':
            pie.operator("edit.tool_settings", depress=(proportional_editing),
                         icon='CHECKBOX_HLT' if proportional_editing else 'CHECKBOX_DEHLT',
                         text="Proportional Editing").mode = 'PROPORTIONAL_EDITING'
        else:
            pie.operator("view3d.rotate_parent", icon='GROUP_BONE')
            # pie.separator()  # Top_right

        pie.operator("bone_collections.hide", icon='BONE_DATA',                                          # Bottom_left
                     text="Hide Collections of Selected").mode = 'SELECTED'

        if not_weight_paint:
            is_rest = (position == 'REST')
            op = pie.operator("wm.context_toggle_enum", icon='BLANK1', depress=(is_rest),             # Bottom_right
                              text="Rest Position" if is_rest else "Pose Position")
            op.data_path = "object.data.pose_position"
            op.value_1 = 'POSE'
            op.value_2 = 'REST'


class MXD_MT_PIE_Armature_SetAndForget(Menu):
    bl_label = "Edit: Armature, Set and Forget"

    def draw(self, context):
        is_edit = (context.mode == 'EDIT_ARMATURE')

        layout = self.layout
        pie = layout.menu_pie()

        if is_edit:
            pie.operator("armature.autoside_names", icon='BLANK1').type = 'XAXIS'        # Left
        else:
            pie.separator()
            # pie.operator("pose.rigify_generate")

        pie.operator("rigify.ik_stretch", icon='BLANK1')                             # Right
        pie.operator("bone_collections.delete_bones", icon='BONE_DATA')                      # Bottom
        pie.operator("armature.one_bbone_segment", icon='BLANK1')                    # Top

        if is_edit:
            pie.operator("armature.symmetrize", icon='BLANK1').direction = 'POSITIVE_X'  # Top_left
        else:
            pie.separator()

        pie.operator("rigify.ik_fk", icon='BLANK1')                                  # Top_right
        pie.separator()  # Bottom_left

        # https://blender.stackexchange.com/questions/43703/how-to-tell-if-an-add-on-is-present-using-python
        if addon_utils.check("rigify") == (True, True):
            target = context.object.data.rigify_target_rig
            text = "Re-Generate Rig" if target else "Generate Rig"
            pie.operator("rigify.generate_wrapper", text=text, icon='POSE_HLT')         # Bottom_right
        else:
            pie.separator()


class MXD_MT_PIE_Pose_ClearTranform(Menu):
    bl_label = "Pose: Armature, Clear Transform"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left
        pie.separator()  # Right
        pie.operator("pose.rot_clear", icon='BLANK1')         # Bottom
        pie.operator("pose.transforms_clear", icon='BLANK1')  # Top
        pie.separator()  # Top_left
        pie.separator()  # Top_right
        pie.operator("pose.loc_clear", icon='BLANK1')         # Bottom_left
        pie.operator("pose.scale_clear", icon='BLANK1')       # Bottom_right


# Modified, properties_data_armature.py
class MXD_DATA_PT_display(Panel):  # (ArmatureButtonsPanel, Panel)
    bl_label = "Viewport Display"
    # bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'  # Added
    bl_region_type = 'WINDOW'  # Added

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # Added; Seems like properties in pop-ups can't be animated

        ob = context.object
        # arm = context.armature
        arm = ob.data

        layout.prop(arm, "display_type", text="Display As")

        col = layout.column(heading="Show")
        col.prop(arm, "show_names", text="Names")
        col.prop(arm, "show_bone_custom_shapes", text="Shapes")
        col.prop(arm, "show_group_colors", text="Group Colors")

        if ob:
            col.prop(ob, "show_in_front", text="In Front")

        col = layout.column(align=False, heading="Axes")
        row = col.row(align=True)
        row.prop(arm, "show_axes", text="")
        sub = row.row(align=True)
        sub.active = arm.show_axes
        sub.prop(arm, "axes_position", text="Position")


class MXD_UL_RotateParentPair(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row()

        split = row.split(factor=0.9)
        sub_split = split.split()
        s_row = sub_split.row()
        s_row.alignment = 'CENTER'
        s_row.label(text=item.name)
        s_row = sub_split.row()
        s_row.alignment = 'CENTER'
        s_row.label(text=item.parent)

        s_row = split.row()
        s_row.alignment = 'RIGHT'
        op = s_row.operator("utils.modify_collection_item", icon='PANEL_CLOSE', emboss=False)
        op.operation = 'REMOVE'
        op.collection = 'bpy.context.preferences.addons[__package__.partition(".")[0]].preferences.armature.bones_parents'
        op.index = index

    def filter_items(self, context, data, property):
        # https://sinestesia.co/blog/tutorials/amazing-uilists-in-blender/
        items = getattr(data, property)
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = UI_UL_list.sort_items_by_name(items, "name")
        return filtered, ordered


class MXD_PT_RotateParentPairs(Panel):
    bl_label = "Rotate Parent"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 20

    def draw(self, context):
        layout = self.layout
        armature = context.preferences.addons[__package__.partition(".")[0]].preferences.armature

        row = layout.row()

        split = row.split(factor=0.9)
        sub_split = split.split()
        s_row = sub_split.row()
        s_row.alignment = 'CENTER'
        s_row.label(text="When this is rotated,...")
        s_row = sub_split.row()
        s_row.alignment = 'CENTER'
        s_row.label(text="...this will also be rotated.")

        split.label(icon='BLANK1')

        layout.template_list("MXD_UL_RotateParentPair", "", armature, "bones_parents", armature, "active_BoneParent", sort_lock=True)


classes = (
    MXD_MT_PIE_Armature,
    MXD_MT_PIE_Pose_ClearTranform,
    MXD_MT_PIE_Armature_SetAndForget,
    MXD_DATA_PT_display,
    MXD_UL_RotateParentPair,
    MXD_PT_RotateParentPairs,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
