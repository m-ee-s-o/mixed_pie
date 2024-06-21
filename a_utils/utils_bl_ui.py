import bpy
from bpy.types import UILayout
from ..f_scripts.scripts_utils import ScriptAppendablePie


class PieWrapper:
    def __init__(self, cls, layout: UILayout):
        self.layout = layout
        self.slices = {"left": None, "right": None, "bottom": None, "top": None, "top_left": None, "top_right": None, "bottom_left": None, "bottom_right": None}
        self.cls = cls

    def __getattribute__(self, name):
        if name in super().__getattribute__("slices"):
            self.direction = name
            return super().__getattribute__("append_to_pie")
        else:
            return super().__getattribute__(name)

    def append_to_pie(self, *args, attr="operator", **kwargs):
        if not (args or kwargs):
            return
        self.slices[self.direction] = (attr, args, kwargs)
        return bpy.context.window_manager.operator_properties_last(args[0])
    
    def draw(self):
        for direction, params in self.slices.items():
            if params is not None:
                attr, args, kwargs = params
                getattr(self.layout, attr)(*args, **kwargs)

            elif issubclass(self.cls, ScriptAppendablePie):
                params = self.cls.direction_occupant[direction]
                if isinstance(params, tuple):
                    op = self.layout.operator("script.execute", text=params[-1], icon='BLANK1')
                    op.category, op.index, op.tooltip = params[:-1]
                else:
                    self.layout.separator()

            else:
                self.layout.separator()
