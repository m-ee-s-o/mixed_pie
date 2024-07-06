import bpy
from .ui_panel_layout import PanelLayout
from .ui_box import Box
from .ui_button import PanelButton


class OperatorProp:
    def __init__(self, id_name):
        super().__setattr__("operator_prop", bpy.context.window_manager.operator_properties_last(id_name))
        super().__setattr__("prop_map", {})

    def __getattribute__(self, name):
        if name not in {"prop_map", "operator_prop"}:
            return getattr(super().__getattribute__("operator_prop"), name)
        else:
            return super().__getattribute__(name)

    def __setattr__(self, __name, __value):
        # Cannot assign properties to operator_prop immediately since layout.draw_structure will be read first before modal.
        # If there are multiple operators of the same type, the last property will be applied even when clicking others before it.
        super().__getattribute__("prop_map")[__name] = __value

class UI_Operator(PanelButton):
    snap_to = Box.snap_to

    def __init__(self, parent, id_name, label, icon, emboss, shortcut):
        self.id_name = id_name
        self.prop = OperatorProp(id_name)
        label = label if label is not None else bpy.context.window_manager.operator_properties_last(id_name).bl_rna.name
        self.initialize_button_ui(parent, label, icon, emboss, shortcut)

    def modal(self, context, event):
        if self.attr_holder.hold:
            return
        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))

        if Box.point_inside(self, event):
            self.color = (0.4, 0.4, 0.4, 1)

            if event.type == 'LEFTMOUSE' and event.value in {'PRESS', 'DOUBLECLICK'}:
                eval("bpy.ops." + self.id_name)(self.root.operator_context, **self.prop.prop_map)
            event.handled = True
