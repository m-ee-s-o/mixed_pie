import bpy
from bpy.types import Operator
from bpy.props import IntProperty, EnumProperty, StringProperty
from .scripts_init import script_categories
from .scripts_utils import ScriptAppendablePie


class MXD_OT_Scripts_Execute(Operator):
    bl_idname = "script.execute"
    bl_label = "Script"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    _appendable_classes = []
    _directions = []

    def callback_get_appendable_classes(self, context):
        _appendable_classes = MXD_OT_Scripts_Execute._appendable_classes
        _appendable_classes.clear()
        for cls in ScriptAppendablePie.subclasses.values():
            _appendable_classes.append((cls.__name__, cls.bl_label, ""))
        return _appendable_classes

    def callback_directions(self, context):
        _directions = MXD_OT_Scripts_Execute._directions
        _directions.clear()
        for direction, occupant in ScriptAppendablePie.subclasses[self.append_to].direction_occupant.items():
            _directions.append((direction, direction.replace('_', ' ').title() + (" (Occupied)" if occupant else ""), ""))
        return _directions

    category: StringProperty(options={'HIDDEN'})
    index: IntProperty(options={'HIDDEN'})
    tooltip: StringProperty(options={'HIDDEN'})
    append_to_pie_as: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    append_to: EnumProperty(name="", items=callback_get_appendable_classes, options={'HIDDEN'})
    direction: EnumProperty(name="", items=callback_directions, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        return '\n' + properties.tooltip
    
    def invoke(self, context, event):
        self.script = script_categories[self.category][self.index]

        if (invoke := getattr(self.script, "invoke", None)):
            if (ret := invoke(self, context, event)):
                return ret

        if self.append_to_pie_as:
            self.draw_popup = True
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        if getattr(self, "draw_popup", False):
            layout = self.layout
            split = layout.split(factor=0.4)

            col = split.column()
            col.alignment = 'RIGHT'
            col.label(text="Append to Pie")
            col.label(text="Direction")

            col = split.column()
            col.prop(self, "append_to")
            col.prop(self, "direction")

    def execute(self, context):
        if self.append_to_pie_as:
            cls = ScriptAppendablePie.subclasses[self.append_to]
            self.report({'INFO'}, f"Added as a <{self.direction}> button to <{cls.bl_label}> pie.")
            cls.direction_occupant[self.direction] = (self.category, self.index, self.tooltip, self.append_to_pie_as)
            return {'CANCELLED'}

        ret = self.script.execute(self, context)
        return ret or {'FINISHED'}


classes = (

    MXD_OT_Scripts_Execute,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
