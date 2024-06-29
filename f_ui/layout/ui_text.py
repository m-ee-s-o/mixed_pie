import bpy
from bpy.types import Panel
from .ui_panel_layout import PanelLayout
from .ui_label import LabelBox
from .ui_box import Box


class TextBox(LabelBox):
    def __init__(self, parent, data, property):
        super().__init__(parent, getattr(data, property))
        self.data_property = (data, property)

    def modal(self, context, event):
        y, h = self.origin.y, self.height
        self.origin.y += self.height / 2
        self.height = min(self.height * 2, self.parent.height)
        PanelLayout.center(self, y=True)
        self.origin.y = y
        self.height = h
        if event.type == 'LEFTMOUSE' and event.value == 'DOUBLECLICK' and Box.point_inside(self, event):
            MXD_PT_Utils_OneTextProp.data_property = self.data_property
            bpy.ops.wm.call_panel(name="MXD_PT_Utils_OneTextProp")
            event.handled = True


class MXD_PT_Utils_OneTextProp(Panel):
    bl_label = "Viewport Display"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        self.layout.prop(*self.data_property, text="")


classes = (
    MXD_PT_Utils_OneTextProp,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
