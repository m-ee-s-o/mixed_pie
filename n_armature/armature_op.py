import bpy
from bpy.types import Operator, SpaceView3D, VIEW3D_HT_header


class MXD_OT_MODAL_RotateParent(Operator):
    bl_idname = "view3d.rotate_parent"
    bl_label = "Rotate Parent"
    active = False

    @classmethod
    def poll(cls, context):
        return (context.area.ui_type == 'VIEW_3D')

    @staticmethod  # since self hear isn't for this class, but for where this is prepended to
    def indicator(self, context):
        self.layout.label(text="RotateParent modal active. (F5 - Add, F6 - Remove, F7 - Close, F8 - List)")

    def invoke(self, context, event):
        if self.__class__.active:
            return {'CANCELLED'}
        self.__class__.active = True

        VIEW3D_HT_header.prepend(self.indicator)

        context.window_manager.modal_handler_add(self)
        self.handler = SpaceView3D.draw_handler_add(self.draw_, (), 'WINDOW', 'POST_PIXEL')

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        if context.mode not in {'PAINT_WEIGHT', 'POSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'R' and event.value == 'PRESS' and not (event.shift or event.ctrl):
            if context.mode == 'PAINT_WEIGHT' and (parent := context.object.parent).type == 'ARMATURE':
                bones = parent.data.bones
            else:
                bones = context.object.data.bones
            
            bones_parents = context.preferences.addons[__package__.partition(".")[0]].preferences.armature.bones_parents
            if (bone_parent := bones_parents.get(bones.active.name)):
                parent = bones[bone_parent.parent]
                parent.select = True
                if event.alt:
                    return {'PASS_THROUGH'}

                context.area.header_text_set(text=str(parent.tail))
                bpy.ops.transform.rotate('INVOKE_DEFAULT', center_override=bpy.data.objects[parent.id_data.name].pose.bones[parent.name].head)
                return {'RUNNING_MODAL'}
            else:
                return {'PASS_THROUGH'}
            
        elif event.type == 'F5' and event.value == 'PRESS':
            if context.mode == 'PAINT_WEIGHT' and (parent := context.object.parent).type == 'ARMATURE':
                bones = parent.data.bones
            else:
                bones = context.object.data.bones

            bones_parents = context.preferences.addons[__package__.partition(".")[0]].preferences.armature.bones_parents
            added = 0
            modified = 0
            for bone in context.selected_pose_bones:
                if bone.bone != bones.active:
                    if (bone_parent := bones_parents.get(bone.name)):
                        bone_parent.parent = bones.active.name
                        modified += 1
                    else:
                        bones_parents.add().set(bone.name, bones.active.name)
                        added += 1
    
            if added or modified:
                bpy.ops.wm.save_userpref()
            
            message = []
            if added:
                message.append(f"Added {added}.")
            if modified:
                message.append(f"Modified {modified}.")
            self.report({'INFO'}, " ".join(message))

        elif event.type == 'F6' and event.value == 'PRESS':
            if context.mode == 'PAINT_WEIGHT' and (parent := context.object.parent).type == 'ARMATURE':
                bones = parent.data.bones
            else:
                bones = context.object.data.bones

            bones_parents = context.preferences.addons[__package__.partition(".")[0]].preferences.armature.bones_parents
            removed = 0
            for bone in context.selected_pose_bones:
                if (index := bones_parents.find(bone.name)) != -1:
                    bones_parents.remove(index)
                    removed += 1
            if removed:
                bpy.ops.wm.save_userpref()

            self.report({'INFO'}, f"Removed {removed}.")

        elif event.type == 'F7' and event.value == 'PRESS':
            self.__class__.active = False
            VIEW3D_HT_header.remove(self.indicator)
            SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            return {'FINISHED'}
        
        elif event.type == 'F8' and event.value == 'PRESS':
            bpy.ops.wm.call_panel(name="MXD_PT_RotateParentPairs")

        else:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def draw_(self):
        ...


classes = (
    MXD_OT_MODAL_RotateParent,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    VIEW3D_HT_header.remove(MXD_OT_MODAL_RotateParent.indicator)
