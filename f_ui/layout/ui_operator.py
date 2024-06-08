import bpy
import blf
from mathutils import Vector
from .ui_panel_layout import PanelLayout
from .ui_box import Box
from .ui_label import LabelBox
from .ui_icon import IconBox


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

class UI_Operator:
    inherit = PanelLayout.inherit
    snap_to = Box.snap_to

    def __init__(self, parent, id_name, label=None, icon=None, emboss=True):
        self.id_name = id_name
        self._prop = OperatorProp(id_name)
        margin = 4
        Box.__init__(self, parent, margin * 2 * parent.ui_scale, (32 + margin * 2) * parent.ui_scale, color=(0.3, 0.3, 0.3, 1))
        self.flow(horizontal=True)
        self.MARGIN = margin
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))
        self.emboss = emboss

        if icon:
            icon = IconBox(self, icon)
            self.width += icon.width * self.ui_scale
        if label is None:
            label = bpy.context.window_manager.operator_properties_last(id_name).bl_rna.name
        if label:
            self.width += blf.dimensions(0, label)[0] + margin
            label_box = LabelBox(self, label)
            label_box.center_y = True

        self.width = max(self.height, self.width)  # If there are no icon and label, match width with height to make it square
        PanelLayout.adjust(self)

    def modal(self, context, event):
        if self.attr_holder.hold:
            return
        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))
        Box.make(self)  # TODO: don't make here
        if Box.point_inside(self, event):
            self.color = (0.4, 0.4, 0.4, 1)

            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                prop = self.prop
                operator_prop = prop.operator_prop
                for property, value in prop.prop_map.items():
                    setattr(operator_prop, property, value)

                eval("bpy.ops." + self.id_name)(self.root.operator_context, **{prop: getattr(operator_prop, prop)
                                                for prop in operator_prop.rna_type.properties.keys() if prop != "rna_type"})
            event.handled = True

    def make(self):
        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))
        Box.make(self)  # Remake; PanelLayout.adjust may change properties after modal's make() like in CollectionItem

    def draw(self):
        if self.emboss:
            Box.draw(self)

    @property
    def prop(self):
        return self._prop
