import bpy
from bpy.types import Operator
import addon_utils


class Base_Rigify_Poll:
    @classmethod
    def poll(cls, context):
        # https://blender.stackexchange.com/questions/43703/how-to-tell-if-an-add-on-is-present-using-python
        enabled_rigify = all(addon_utils.check("rigify"))
        rig_id = context.object.data.get('rig_id')
        mode = (context.mode == 'POSE')
        if not enabled_rigify:
            cls.poll_message_set('"Rigify" addon not enabled.')
        elif not rig_id:
            cls.poll_message_set('Rigify "rig_id" property not found. Rig must be generated by rigify.')
        elif not mode:
            cls.poll_message_set("Mode must be Pose.")
        return enabled_rigify and rig_id and mode


class MXD_OT_Armature_Rigify_GenerateWrapper(Base_Rigify_Poll, Operator):
    bl_idname = "rigify.generate_wrapper"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Wrapper of Rigify Generate Operator.\n\n"     \
                     "Changes:\n"                                   \
                     "    Start with FK.\n"                         \
                     "    IK Stretch disabled.\n"                   \
                     "    BBone Segments to 1.\n"                   \
                     '    Retain "locked" states.\n'                \
                     "    Retain location, rotation and scale.\n"   \
                     "    Retain pose position.\n"   \
                     "    Retain non-rigify-generated constraints"  \

    @classmethod
    def poll(cls, context):
        return bpy.ops.pose.rigify_generate.poll()

    def invoke(self, context, event):
        obj = context.object
        
        locked_visible = None
        if (target_rig := obj.data.rigify_target_rig):
            all_bcolls = target_rig.data.collections_all
            pose_position = target_rig.data.pose_position
            locked_visible = {b_coll.name: (b_coll.MixedPie.locked, b_coll.is_visible) for b_coll in all_bcolls}
            bones_rotLocScale_constraints = {}
            for bone in target_rig.pose.bones:
                rotLocScale_constraints = [{}, []]
                for mode in ("rotation_quaternion", "rotation_euler", "rotation_axis_angle", "location", "scale"):
                    rotLocScale_constraints[0][mode] = tuple(getattr(bone, mode))

                for constraint in bone.constraints:
                    props = {}
                    for prop in constraint.bl_rna.properties:
                        if not prop.is_readonly:
                            props[prop.identifier] = getattr(constraint, prop.identifier)
                    rotLocScale_constraints[1].append((constraint.type, props))

                bones_rotLocScale_constraints[bone.name] = rotLocScale_constraints

        result = bpy.ops.pose.rigify_generate()
        if result == {'FINISHED'} and locked_visible:
            target_rig.data.pose_position = pose_position

            for name, (locked, visible) in locked_visible.items():
                all_bcolls[name].MixedPie.locked = locked
                all_bcolls[name].is_visible = visible
            
            for name, (rotLocScale, constraints) in bones_rotLocScale_constraints.items():
                bone = target_rig.pose.bones[name]
                for attr, value in rotLocScale.items():
                    setattr(bone, attr, value)

                b_constraints = bone.constraints
                for type, constraint in constraints:
                    if not constraint:
                        continue
                    if constraint['name'] in b_constraints:
                        continue
                    new_contraint = b_constraints.new(type)
                    for prop, value in constraint.items():
                        setattr(new_contraint, prop, value)

        target_rig = target_rig or bpy.data.objects[bpy.data.armatures[-1].name]
        if target_rig:
            for p_bone in target_rig.pose.bones:
                if p_bone.get("IK_FK") is not None:
                    p_bone["IK_FK"] = 1
                if p_bone.get("IK_Stretch") is not None:
                    p_bone["IK_Stretch"] = 0
                p_bone.bone.bbone_segments = 1

        obj.hide_set(True)
        return result
        

class MXD_OT_Armature_Rigify_IK_FK(Base_Rigify_Poll, Operator):
    bl_idname = "rigify.ik_fk"
    bl_label = "IK/FK"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Set rigify's bone IK/FK switch of selected pose parent bones to 1 (FK).\n\n"  \
                     "Shift: Set it to 0 (IK) instead"

    def invoke(self, context, event):
        set_property(self, context, event, 'IK_FK', (1.0, 0.0), ("FK", "IK"))
        return {'FINISHED'}


def set_property(self, context, event, prop_name, values, value_description, set=True):
    counter = 0
    for bone in context.selected_pose_bones:
        if bone.get(prop_name) is not None:
            bone[prop_name] = values[0] if not event.shift else values[1]
            counter += 1

    # Redraw if rigify panel is open since it won't sync automatically
    if context.space_data.show_region_ui:
        for region in context.area.regions:
            if region.type == 'UI':
                region.tag_redraw()

    property = "properties" if (counter > 1) else "property"
    value = value_description[0] if not event.shift else value_description[1]
    if set:
        self.report({'INFO'}, f"Set {counter} '{prop_name}' {property} to {value}")
    else:
        self.report({'INFO'}, f"{value} {counter} '{prop_name}' {property}")


class MXD_OT_Armature_Rigify_IKStretch(Base_Rigify_Poll, Operator):
    bl_idname = "rigify.ik_stretch"
    bl_label = "IK Stretch"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Set rigify's bone IK stretch of selected pose parent bones to 0 (disabled).\n\n"  \
                     "Shift: Set it to 1 (enabled) instead"

    def invoke(self, context, event):
        set_property(self, context, event, 'IK_Stretch', (0.0, 1.0), ("Disabled", "Enabled"), set=False)
        return {'FINISHED'}


class MXD_OT_Armature_OneBBoneSegment(Operator):
    bl_idname = "armature.one_bbone_segment"
    bl_label = "Set B-Bone Segment to 1"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Set bendy bone segment of all bones in armature to 1.\n"      \
                     "If the bone is a rigify type and part of a metarig, also set its bendy bone segment option to 1"

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.6)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        if self.counter or not self.rigify_counter:
            col1.label(text="Modified Bone Properties:")
            col2.label(text=f"{self.counter}")

        if self.rigify_counter:
            col1.label(text="Modified Rigify Properties:")
            col2.label(text=f"{self.rigify_counter}")

    def execute(self, context):
        self.counter = 0
        self.rigify_counter = 0
        obj = context.object
        data = obj.data
        pose_bones = obj.pose.bones
        bones = data.bones if (context.mode == 'POSE') else data.edit_bones
        for bone in bones:
            if bone.bbone_segments != 1:
                bone.bbone_segments = 1
                self.counter += 1
            if (params := getattr(pose_bones[bone.name], "rigify_parameters", None)):
                if params.bbones != 1:
                    params.bbones = 1
                    self.rigify_counter += 1
        return {'FINISHED'}


classes = (
    MXD_OT_Armature_Rigify_GenerateWrapper,
    MXD_OT_Armature_Rigify_IK_FK,
    MXD_OT_Armature_Rigify_IKStretch,
    MXD_OT_Armature_OneBBoneSegment,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)