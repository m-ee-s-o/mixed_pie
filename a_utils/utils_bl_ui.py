from bpy.types import UILayout
from ..f_scripts.scripts_utils import ScriptAppendablePie
from ..f_ui.layout.ui_operator import OperatorProp


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

    def append_to_pie(self, *args, **kwargs):
        if not (args or kwargs):
            return
        args = list(args)
        attr = args.pop(0) if isinstance(args[0], str) and hasattr(self.layout, args[0]) else "operator"

        self.slices[self.direction] = [attr, args, kwargs, None]

        if attr == "operator":
            self.slices[self.direction][3] = OperatorProp(args[0])
            return self.slices[self.direction][3]
    
    def draw(self):
        for direction, params in self.slices.items():
            if params is not None:
                attr, args, kwargs, operator_prop = params
                op = getattr(self.layout, attr)(*args, **kwargs)
                if attr == "operator":
                    for prop, value in operator_prop.prop_map.items():
                        setattr(op, prop, value)

            elif issubclass(self.cls, ScriptAppendablePie):
                params = self.cls.direction_occupant[direction]
                if isinstance(params, tuple):
                    op = self.layout.operator("script.execute", text=params[-1], icon='BLANK1')
                    op.category, op.index, op.tooltip = params[:-1]
                else:
                    self.layout.separator()

            else:
                self.layout.separator()
