import bpy
from bpy.types import Operator
from bpy.props import BoolVectorProperty, FloatProperty, StringProperty


class Base_Modifier_Poll:
    @classmethod
    def poll(cls, context):
        obj = context.object
        obj_type = (obj.type in cls.obj_types) if obj else False
        not_pt = (context.mode != 'PAINT_TEXTURE')
        not_pt = (not_pt or getattr(cls, "paint_tex", True))
        if not obj:
            cls.poll_message_set("Object not found.")
        elif not obj_type:
            cls.poll_message_set(cls.obj_types_msg)
        elif not not_pt:
            cls.poll_message_set("Mode mustn't be Texture Paint, undo doesn't work.")
        return obj and obj_type and not_pt


def set_name(event, name, objs):
    suffix_counter = 0
    name = name.removesuffix('(IH)') if event.shift else f"_{name}"  # "_" separates preconfigured and normal
    mod_name = name
    modifier_names = set()
    for obj in objs:
        for modifier in obj.modifiers:
            if modifier.name.startswith(name):
                modifier_names.add(modifier.name)
    while True:
        if mod_name in modifier_names:
            suffix_counter += 1
            mod_name = f"{name}.{suffix_counter:03}"
        else:
            break
    return mod_name


class MXD_OT_Modifier(Base_Modifier_Poll, Operator):
    bl_idname = "modifier.add"
    bl_label = "Add Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    obj_types = {'MESH', 'CURVE', 'FONT', 'SURFACE'}
    obj_types_msg = "Object type must be Mesh, Curve, Font, or Surface."
    modifier: StringProperty()

    @classmethod
    def description(cls, context, properties):
        return f"Add a preconfigured {properties.modifier} modifier to all selected objects.\n\n"  \
                "Shift: Add without preconfigured parameters"

    def invoke(self, context, event):
        if context.mode == 'SCULPT':
            bpy.ops.ed.undo_push(message='Before "Add Modifier"')  # ?: Doesn't work in 'PAINT_TEXTURE' mode
        match self.modifier:
            case "mirror":
                self.add_modifier(context, event, "Mirror", 'MIRROR', True, False)
            case "subdivision surface":
                self.add_modifier(context, event, "Subdivision", 'SUBSURF', False, False)
            case "solidify (for inverted hull)":
                self.add_modifier(context, event, "Solidify(IH)", 'SOLIDIFY', True, False)
        return {'FINISHED'}

    def add_modifier(self, context, event, name, mod_type, show_on_cage, show_expanded):
        self.objs = {obj for obj in context.selected_objects if obj.type in self.obj_types}
        self.objs.add(context.object)
        mod_name = set_name(event, name, self.objs)
        for obj in self.objs:
            mod = obj.modifiers.new(mod_name, type=mod_type)
            if not event.shift:
                mod.show_on_cage = show_on_cage
                mod.show_expanded = show_expanded
                match name:
                    case "Mirror":
                        mod.use_bisect_axis[0] = True
                        mod.use_clip = True
                        mod.merge_threshold = 0.00001
                        mod.bisect_threshold = 0.00001
                    case "Subdivision":
                        mod.render_levels = 1
                    case "Solidify(IH)":
                        if (index := obj.data.materials.find("Outline")) == -1:
                            bpy.ops.material.preset(type='OUTLINE')
                            index = obj.data.materials.find("Outline")

                        mod.thickness = 0.0005
                        mod.offset = 1.0
                        mod.use_flip_normals = True
                        mod.use_quality_normals = True
                        mod.material_offset = index
                        mod.material_offset_rim = 1

        self.len_ = len(self.objs)
        self.report({'INFO'}, f"Added {mod.name} to {self.len_} object{'s' if self.len_ > 1 else ''}.")

        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.spaces[0].context = 'MODIFIER'


class MXD_OT_Modifier_Symmetrize(Base_Modifier_Poll, Operator):
    bl_idname = "modifier.symmetrize"
    bl_label = "Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Mirror and apply"

    obj_types = {'MESH'}
    obj_types_msg = "Object type must be Mesh, Curve, Font, or Surface."
    paint_tex = False

    axis: BoolVectorProperty(name="", subtype='XYZ')
    bisect: BoolVectorProperty(name="", subtype='XYZ')
    flip: BoolVectorProperty(name="", subtype='XYZ', options={'SKIP_SAVE'})
    bisect_distance: FloatProperty(name="", precision=5, min=0, soft_max=1, default=0.00001)

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        col1.label(text="Axis")
        col2.row().prop(self, "axis", toggle=True)

        col1.label(text="Bisect")
        col2.row().prop(self, "bisect", toggle=True)

        col1.label(text="Flip")
        col2.row().prop(self, "flip", toggle=True)

        col1.separator()
        col2.separator()

        col1.label(text="Bisect Distance")
        col2.prop(self, "bisect_distance")

    def invoke(self, context, event):
        if context.mode == 'SCULPT':
            bpy.ops.ed.undo_push(message=f'Before "{self.bl_label}"')
        self.shift = True
        ret = self.execute(context)
        self.report({'INFO'}, f"Applied to {self.len_} object{'s' if self.len_ > 1 else ''}.")        
        return ret

    def execute(self, context):
        self.objs = {obj for obj in context.selected_objects if obj.type in self.obj_types}
        self.objs.add(context.object)
        mod_name = set_name(self, "Mirror", self.objs)
        for obj in self.objs:
            mod = obj.modifiers.new(mod_name, type='MIRROR')
            mod.use_axis = self.axis
            mod.use_bisect_axis = self.bisect
            mod.use_bisect_flip_axis = self.flip
            mod.merge_threshold = 0.0001
            mod.bisect_threshold = self.bisect_distance
        self.len_ = len(self.objs)

        if context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.apply_modifier(context, mod_name)
            bpy.ops.object.mode_set(mode='EDIT')                    
        else:
            self.apply_modifier(context, mod_name)
        return {'FINISHED'}

    def apply_modifier(self, context, mod_name):
        for obj in self.objs:
            for modifier in obj.modifiers:
                if modifier.name == mod_name:
                    with context.temp_override(object=obj):
                        bpy.ops.object.modifier_apply(modifier=mod_name)


class MXD_OT_Modifier_DataTransfer(Base_Modifier_Poll, Operator):
    bl_idname = "modifier.add_data_transfer"
    bl_label = "Add Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add a preconfigured data transfer modifier to all selected objects.\n\n"  \
                     "Shift: Add without preconfigured parameters"

    obj_types = {'MESH'}
    obj_types_msg = "Object type must be Mesh."

    def invoke(self, context, event):
        if context.mode == 'SCULPT':
            bpy.ops.ed.undo_push(message='Before "Add Modifier"')
        objs = {obj for obj in context.selected_objects if obj.type == 'MESH'}
        objs.add(context.object)
        mod_name = set_name(event, "DataTransfer", objs)
        for obj in objs:
            mod = obj.modifiers.new(mod_name, type='DATA_TRANSFER')
            if not event.shift:
                mod.use_vert_data = True
                mod.data_types_verts = {'VGROUP_WEIGHTS'}
                mod.vert_mapping = 'POLYINTERP_NEAREST'
        len_ = len(objs)
        self.report({'INFO'}, f"Added {mod.name} to {len_} object{'s' if len_ > 1 else ''}.")
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.spaces[0].context = 'MODIFIER'
        return {'FINISHED'}


classes = (
    MXD_OT_Modifier,
    MXD_OT_Modifier_Symmetrize,
    MXD_OT_Modifier_DataTransfer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
