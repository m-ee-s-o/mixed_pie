import bpy
from bpy.types import Operator, UIList
from bpy.props import CollectionProperty, IntProperty, StringProperty
from .bone_collections_prop import MXD_CollT_PathToBoneCollection, MXD_CollT_ItemForColumn


class MXD_UL_IncludedBoneCollections(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        layout.prop(item, "include", icon='CHECKBOX_HLT' if item.include else 'CHECKBOX_DEHLT', emboss=False)
        layout.label(text=item.coll_name)


class Base_BoneCollectionsOps:
    report_message = "report"
    active_index: IntProperty()
    included: CollectionProperty(type=MXD_CollT_PathToBoneCollection)

    @staticmethod
    def poll_check_for_armature(cls, context):
        # Separated since another operator also uses this
        for obj in {*(context.selected_objects), context.object}:
            if obj.type == 'ARMATURE':
                break
        else:
            cls.poll_message_set("No selected armature found.")
            return False
        if context.mode not in {'POSE', 'PAINT_WEIGHT', 'EDIT_ARMATURE', getattr(cls, 'add_mode', None)}:
            return False
        return True

    @classmethod
    def poll(cls, context):
        return cls.poll_check_for_armature(cls, context)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.text)
        layout.template_list("MXD_UL_IncludedBoneCollections", "",
                             self, "included",
                             self, "active_index"
                             )

    def invoke(self, context, event):
        self.included.clear()

        mode_changed = False
        obj_changed = False
        mode = context.mode
        if context.object.type != 'ARMATURE':
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    obj_changed = True
                    org_object =  context.object
                    context.view_layer.objects.active = obj
                    break
        if mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
            mode_changed = True

        sel_bones_names = {bone.name for bone in context.selected_pose_bones}

        for obj in {*context.selected_objects, context.object}:
            if obj.type == 'ARMATURE':
                for bcoll in obj.data.collections_all:
                    if not bcoll.MixedPie.locked:
                        if not self.include(bcoll, sel_bones_names):
                            continue
                        self.included.add().set(obj.name, bcoll.name)

        if obj_changed:
            context.view_layer.objects.active = org_object
        if mode_changed:
            bpy.ops.object.mode_set(mode=mode.split('_')[0] if mode != 'PAINT_WEIGHT' else 'WEIGHT_PAINT')
        if not self.included:
            self.report({'INFO'}, self.report_message)
            return {'CANCELLED'}
        return self.execute(context)


class MXD_OT_Armature_BoneCollections_ShowAll(Base_BoneCollectionsOps, Operator):
    bl_idname = "bone_collections.show_all"
    bl_label = "Show All Collections"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Show all collections excluding locked ones"

    report_message = "No collection/s to show."
    add_mode = 'OBJECT'
    text = "Shown collections:"

    def include(self, bcoll, sel_bones_names):
        """ Only show bone collection if it is not visible """
        return not bcoll.is_visible

    def execute(self, context):
        for i in self.included:
            if i.include:
                bpy.data.objects[i.obj_name].data.collections_all[i.coll_name].is_visible = True
        return {'FINISHED'}


class MXD_OT_Armature_BoneCollections_Hide(Base_BoneCollectionsOps, Operator):
    bl_idname = "bone_collections.hide"
    bl_label = "Hide Bone Collections"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    report_message = "No selected bone/s."
    text = "Hidden collections:"

    mode: StringProperty()

    def include(self, bcoll, sel_bones_names):
        """
        If 'SELECTED', only hide the collection in which the bone belongs to,
        else if it's EXCEPT_SELECTED', only hide collections where bone doesn't belong to.
        """
        if not bcoll.is_visible:  # No need to hide already hidden collections
            return False

        for bone in bcoll.bones:
            if bone.name in sel_bones_names:
                ret = True
                break
        else:
            ret = False

        if self.mode == 'SELECTED':
            return ret
        else:
            return not ret

    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'SELECTED':
                return "Hide the bone collections of all selected bones.\n"   \
                       "Exclude locked collections"
            case 'EXCEPT_SELECTED':
                return "Hide all bone collections except selected bones'.\n"  \
                       "Exclude locked collections"

    def execute(self, context):
        for i in self.included:
            if i.include:  # Is here since user can uninclude what's in self.included through last operator panel
                bpy.data.objects[i.obj_name].data.collections_all[i.coll_name].is_visible = False

        return {'FINISHED'}


class MXD_OT_Armature_BoneCollections_DeleteBones(Base_BoneCollectionsOps, Operator):
    bl_idname = "bone_collections.delete_bones"
    bl_label = "Delete Selected's Collections"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = "Delete all bones in selected bones' collection.\n"  \
                     "Exclude locked"

    report_message = "No selected bone/s."
    text = "Delete Bone Collections"
    add_mode = 'EDIT_ARMATURE'

    def include(self, bcoll, sel_bones_names):
        """ Only delete bone collections in which selected bones belongs to. """
        for bone in bcoll.bones:
            if bone.name in sel_bones_names:
                return True
        return False

    def execute(self, context):
        edit_armature = False
        if context.mode == 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='POSE')
            edit_armature = True

        for i in self.included:
            if i.include:
                i['bone_names'] = [bone.name for bone in bpy.data.objects[i.obj_name].data.collections_all[i.coll_name].bones]

        if context.mode == 'POSE':
            bpy.ops.object.mode_set(mode='EDIT')

        for i in self.included:
            if i.include:
                edit_bones = bpy.data.objects[i.obj_name].data.edit_bones
                for name in i['bone_names']:
                    edit_bones.remove(edit_bones[name])

        bpy.ops.object.mode_set(mode='POSE')

        for i in self.included:
            if i.include:
                data = bpy.data.objects[i.obj_name].data
                data.collections.remove(data.collections_all[i.coll_name])

        if edit_armature:
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class MXD_UL_ItemForColumn(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        b_coll = eval(item.bone_collection)
        layout.prop(item, "include", icon='CHECKBOX_HLT' if item.include else 'CHECKBOX_DEHLT', emboss=False)
        if item.generation != 0:
            row = layout.row()
            row.alignment = 'LEFT'
            for _ in range(item.generation):
                row.label(text=" ")
        layout.label(text=b_coll.name)


def get_bone_collection_family(parent, family=None, generation=0):
    family = family or []
    if not parent.children:
        return family
    generation += 1
    for child in parent.children:
        family.append((child, generation))
        get_bone_collection_family(child, family, generation)
    return family


class MXD_OT_Armature_BoneCollections_SelectItemsForColumn(Operator):
    bl_idname = "bone_collections.select_items_for_column"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = ""

    collection: StringProperty(options={'SKIP_SAVE'})
    bone_collections: CollectionProperty(type=MXD_CollT_ItemForColumn, options={'SKIP_SAVE'})
    active_index: IntProperty()
    
    def invoke(self, context, event):
        for b_coll in context.object.data.collections:
            bc = self.bone_collections.add()
            bc.generation = 0
            bc.bone_collection = repr(b_coll)
            for child, generation in get_bone_collection_family(b_coll):
                bc = self.bone_collections.add()
                bc.generation = generation
                bc.bone_collection = repr(child)
        return context.window_manager.invoke_props_popup(self, event)

    def draw(self, context):
        self.layout.template_list("MXD_UL_ItemForColumn", "", self, "bone_collections", self, "active_index", rows=10, sort_lock=True)

    def execute(self, context):
        collection = eval(self.collection)
        for i in self.bone_collections:
            if i.include:
                name = eval(i.bone_collection).name
                if name not in collection:
                    collection.add().name = name
        return {'FINISHED'}


classes = (
    MXD_UL_IncludedBoneCollections,
    MXD_OT_Armature_BoneCollections_ShowAll,
    MXD_OT_Armature_BoneCollections_Hide,
    MXD_OT_Armature_BoneCollections_DeleteBones,
    MXD_UL_ItemForColumn,
    MXD_OT_Armature_BoneCollections_SelectItemsForColumn,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
