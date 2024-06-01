import bpy
from bpy.types import Menu


class MXD_MT_PIE_Object(Menu):
    bl_label = "Object"

    def draw(self, context):
        obj = context.object
        tool_settings = context.scene.tool_settings
        snap = tool_settings.use_snap
        proportional_editing = tool_settings.use_proportional_edit_objects
        armature = obj and (obj.type == 'ARMATURE')

        layout = self.layout
        pie = layout.menu_pie()

        if armature:
            pie.operator("bone_collections.show_all", icon='BLANK1')                                   # Left
        else:
            pie.separator()

        pie.separator()  # Right
        pie.separator()  # Bottom

        pie.operator("mode.use_snap", depress=(snap),                                                 # Top
                     icon='CHECKBOX_HLT' if snap else 'CHECKBOX_DEHLT')

        if armature:
            pie.operator("bone_collections_panel.invoke", icon='BONE_DATA')
            # pie.operator("wm.call_panel", icon='BONE_DATA',                                           # Top_left
                        #  text="Bone Layers").name = "MXD_PT_Armature_BoneCollectionsPanel"
        else:
            pie.separator()

        pie.operator("object.use_proportional_editing", depress=(proportional_editing),               # Top_right
                     icon='CHECKBOX_HLT' if proportional_editing else 'CHECKBOX_DEHLT')

        pie.separator()  # Bottom_left

        if armature:
            position = obj.data.pose_position
            op = pie.operator("wm.context_toggle_enum", icon='BLANK1', depress=(position == 'REST'),  # Bottom_right
                              text="Pose Position" if (position == 'POSE') else 'Rest Position')
            op.data_path = "object.data.pose_position"
            op.value_1 = 'POSE'
            op.value_2 = 'REST'
        else:
            pie.separator()


class MXD_MT_PIE_Object_ClearTransform(Menu):
    bl_label = "Object, Clear Transform"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.separator()  # Left
        pie.separator()  # Right
        pie.operator("object.rotation_clear", icon='BLANK1')        # Bottom
        op = pie.operator("object.clear_transform", icon='BLANK1')  # Top
        op.location, op.rotation, op.scale = True, True, True
        pie.separator()  # Top_left
        pie.separator()  # Top_right
        pie.operator("object.location_clear", icon='BLANK1')        # Bottom_left
        pie.operator("object.scale_clear", icon='BLANK1')           # Bottom_right


classes = (
    MXD_MT_PIE_Object,
    MXD_MT_PIE_Object_ClearTransform,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
