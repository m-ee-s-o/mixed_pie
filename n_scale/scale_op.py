import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty


class MXD_OT_3D_ScaleXYZby(Operator):
    bl_idname = "scale.xyz_3d"
    bl_label = "ScaleXYZby"
    bl_options = {'REGISTER', 'UNDO'}

    x: FloatProperty(name="", precision=3, default=1, options={'SKIP_SAVE'})
    y: FloatProperty(name="", precision=3, default=1, options={'SKIP_SAVE'})
    z: FloatProperty(name="", precision=3, default=1, options={'SKIP_SAVE'})
    pivot_cursor: BoolProperty(
        name="", options={'SKIP_SAVE'},
        description="If current transform pivot point is not the 3D Cursor, "
                    "change it to be it, and then change it back")

    @classmethod
    def description(cls, context, properties):
        scales = (('X', properties.x), ('Y', properties.y), ('Z', properties.z))
        description = []
        for axis, scale in scales:
            if scale != 1:
                description.append(f"Scale selection along {axis} axis by {scale:.3f}")
        return ".\n".join(description)

    @classmethod
    def poll(cls, context):
        mode = (context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE',
                                 'EDIT_ARMATURE', 'EDIT_LATTICE', 'POSE'})
        if not (obj := context.object):
            cls.poll_message_set("Object not found.")
        elif not mode:
            cls.poll_message_set("Mode must be Object, Edit: Mesh, Edit: Curve, "
                                 "Edit: Surface, Edit: Armature, Edit: Lattice, or Pose")
        return obj and mode

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)

        x = col.row()
        x.prop(self, "x", text="X")
        x.active = True if self.x != 1 else False

        y = col.row()
        y.prop(self, "y", text="Y")
        y.active = True if self.y != 1 else False

        z = col.row()
        z.prop(self, "z", text="Z")
        z.active = True if self.z != 1 else False

        layout.prop(self, "pivot_cursor", text="Pivot: 3D Cursor", icon='PIVOT_CURSOR', toggle=True)

    def execute(self, context):
        scale = (self.x, self.y, self.z)
        if self.pivot_cursor:
            if context.scene.tool_settings.transform_pivot_point != 'CURSOR':
                current = context.scene.tool_settings.transform_pivot_point
                context.scene.tool_settings.transform_pivot_point = 'CURSOR'
                bpy.ops.transform.resize(value=scale)
                context.scene.tool_settings.transform_pivot_point = current
                return {'FINISHED'}
        bpy.ops.transform.resize(value=scale)
        return {'FINISHED'}


class MXD_OT_2D_ScaleXYZby(Operator):
    bl_idname = "scale.xyz_2d"
    bl_label = "ScaleXYZby"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    x: FloatProperty(name="", precision=3, default=1, options={'SKIP_SAVE'})
    y: FloatProperty(name="", precision=3, default=1, options={'SKIP_SAVE'})
    pivot_cursor: BoolProperty(
        name="", default=True,  # options={'SKIP_SAVE'},
        description="If current transform pivot point is not the 3D Cursor, "
                    "change it to be it, and then change it back")

    @classmethod
    def description(cls, context, properties):
        scales = (('X', properties.x), ('Y', properties.y))
        description = []
        for axis, scale in scales:
            if scale != 1:
                description.append(f"Scale selection along {axis} axis by {scale:.3f}")
        return ".\n".join(description) + ".\n\nShift: Toggle Pivot Cursor"

    @classmethod
    def poll(cls, context):
        if context.area.ui_type.endswith("NodeTree"):
            if not context.space_data.edit_tree:
                cls.poll_message_set("No active node tree.")
                return False
            if not context.selected_nodes:
                cls.poll_message_set("No selected nodes.")
                return False
        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=True)

        x = col.row()
        x.prop(self, "x", text="X")
        x.active = True if self.x != 1 else False

        y = col.row()
        y.prop(self, "y", text="Y")
        y.active = True if self.y != 1 else False

        layout.prop(self, "pivot_cursor", text="Pivot: 3D Cursor", icon='PIVOT_CURSOR', toggle=True)

    def invoke(self, context, event):
        if event.shift:
            self.pivot_cursor = not self.pivot_cursor
        return self.execute(context)

    def execute(self, context):
        scale = (self.x, self.y, 1)
        if self.pivot_cursor and (context.area.ui_type == 'UV'):
            if context.space_data.pivot_point != 'CURSOR':
                current = context.space_data.pivot_point
                context.space_data.pivot_point = 'CURSOR'
                bpy.ops.transform.resize(value=scale)
                context.space_data.pivot_point = current
                return {'FINISHED'}
        bpy.ops.transform.resize(value=scale)
        return {'FINISHED'}


classes = (
    MXD_OT_3D_ScaleXYZby,
    MXD_OT_2D_ScaleXYZby,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
