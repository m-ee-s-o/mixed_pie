import blf
from mathutils import Vector
from .ui_panel_layout import PanelLayout
from .ui_box import Box, Bounds
from .ui_label import LabelBox
from .ui_icon import IconBox
from .ui_operator import UI_Operator
from ...a_utils.utils_func import recur_get_bone_collections


class Prop(Bounds):
    inherit = PanelLayout.inherit
    make = UI_Operator.make
    draw = UI_Operator.draw
    snap_to = Box.snap_to

    def __init__(self, parent, data, property, label=None, icon=None, emboss=True):
        self.data = data
        self.property = property
        self.init(parent, label, icon, emboss)

    def init(self, parent, label, icon, emboss):
        margin = 4
        Box.__init__(self, parent, margin * 2 * parent.ui_scale, (32 + margin * 2) * parent.ui_scale, color=(0.3, 0.3, 0.3, 1))
        self.flow(horizontal=True)
        self.MARGIN = margin
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))
        self.emboss = emboss

        if icon:
            self.icon_box = IconBox(self, icon)
            self.width += self.icon_box.width * self.ui_scale
        if label:
            self.width += blf.dimensions(0, label)[0] + margin
            self.label_box = LabelBox(self, label)
            self.label_box.center_y = True
        self.width = max(self.height, self.width)
        if icon and label:
            PanelLayout.adjust(self)

    def modal(self, context, event):
        if getattr(self, "dud", None):
            return
        if self.attr_holder.hold:
            return
        prop_id = f"{self.data.__class__.__name__}.{self.property}"
        if (id_ := self.attr_holder.drag[0]):
            if event.type == 'MOUSEMOVE' and id_ != prop_id:
                return
            elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.attr_holder.drag = ("", "")
                event.handled = True

        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))

        match self.data.bl_rna.properties[self.property].type:
            case 'BOOLEAN':
                if Box.point_inside(self, event):
                    self.color = (0.4, 0.4, 0.4, 1)

                    if event.type == 'LEFTMOUSE':
                        if event.value == 'PRESS':
                            self.value = not getattr(self.data, self.property)
                            setattr(self.data, self.property, self.value)
                            self.attr_holder.drag = (prop_id, self.value)
                            event.handled = 'CLICKED'
                    elif event.type == 'MOUSEMOVE' and id_:
                        setattr(self.data, self.property, self.attr_holder.drag[1])
                        event.handled = True


class CollectionProp(Prop):
    def __init__(self, parent, collection, item, property_path, label=None, icon=None, emboss=True):
        self.base, _, self.property = property_path.rpartition(".")
        self.item = item
        self.data = item.path_resolve(self.base) if self.base else item
        self.collection = collection
        self.init(parent, label, icon, emboss)

    def modal(self, context, event):
        super().modal(context, event)
        # Specifically for bone collections as of now
        if self.collection.bl_rna.identifier != "BoneCollections":
            return
        if event.handled == 'CLICKED':
            if event.shift:
                for i in recur_get_bone_collections(self.collection):
                    setattr(i.path_resolve(self.base) if self.base else i, self.property, self.value)
            elif event.alt:
                for i in recur_get_bone_collections(self.collection):
                    if i != self.item:
                        setattr(i.path_resolve(self.base) if self.base else i, self.property, self.value)
                    else:
                        setattr(self.data, self.property, not self.value)
