import time
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ..utils.utils_box import make_box
from .ui_box import Box
from .ui_icon import IconBox
from .ui_panel_layout import PanelLayout
from .ui_label import LabelBox
from .ui_box import Bounds


counters = {}


class PanelButton(Bounds):
    def initialize_button_ui(self, parent, label, icon, emboss, shortcut):
        margin = 4
        Box.__init__(self, parent, margin * 2 * parent.ui_scale, (32 + margin * 2) * parent.ui_scale, color=(0.3, 0.3, 0.3, 1))
        self.flow(horizontal=True)
        self.MARGIN = margin
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))
        self.emboss = emboss

        if icon:
            icon = IconBox(self, icon)
            self.width += icon.width * self.ui_scale
        if label:
            self.width += blf.dimensions(0, label)[0] + self.MARGIN
            lbl = LabelBox(self, label)
            lbl.center_y = True
        if shortcut:
            self.width += blf.dimensions(0, shortcut)[0] + self.MARGIN
            lbl = LabelBox(self, shortcut)
            lbl.center_y = True
            lbl.label_color = (0.7, 0.7, 0.7, 1)
            lbl.adjustable = False

        self.width = max(self.height, self.width)  # If there are no icon and label, match width with height to make it square

    def __init__(self, parent, label, func, icon, emboss, shortcut):
        self.initialize_button_ui(parent, label, icon, emboss, shortcut)
        self.func = func

    def modal(self, context, event):
        if self.attr_holder.hold:
            return
        if Box.point_inside(self, event):
            if not self.emboss:
                self.emboss = True
            else:
                self.color = (self.color[0] * 1.2, self.color[1] * 1.2, self.color[2] * 1.2, self.color[3])
            self.emboss = True
            if event.type == 'LEFTMOUSE' and event.value in {'PRESS', 'DOUBLECLICK'}:
                self.func()

    def make(self):
        # Modal's execution of the following will be skipped if there's hold, so make sure to put these here.
        # Also, PanelLayout.adjust may change properties after modal's make() like in CollectionItem
        PanelLayout.adjust(self)
        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))
        Box.make(self)

    def draw(self):
        if self.emboss:
            Box.draw(self)


class PieButton(Bounds):
    make = Box.make

    def __init__(self, parent, id, label, desciptor):
        Box.__init__(self, parent, 0, 0, color=(0, 0, 0, 1))
        self.is_active = False
        self.id = id
        self.button_label = Box.label(self, label)
        self.height = self.button_label.height + self.MARGIN * 2
        self.width = self.height
        self.origin_point = 'CENTER'
        self.description_text = desciptor(self) if desciptor else "None"
        self.text_size = self.root.text_size

    def modal(self, context, event):
        if self.is_active:
            if self.id not in counters:
                counters[self.id] = time.time()
            elif time.time() - counters[self.id] >= 0.75:
            # else:
                pre_text_size = self.root.text_size
                self.root.text_size = self.text_size
                description = Box(self, 0, 0, color=(0, 0, 0, 1))
                # lbl = description.label(time.time() - counters[self.id])
                height = width = 0
                for i, txt in enumerate(self.description_text.split("\n")):
                    if i != 0:  # Change spacing between lines
                        description.MARGIN = 4
                        description.vMARGIN_TOP_LEFT = Vector((-description.MARGIN, description.MARGIN))

                    lbl = description.label(txt)
                    height += lbl.height + description.MARGIN
                    if lbl.width > width:
                        width = lbl.width

                description.bevel_radius = 4
                description.width = width + self.MARGIN * 2
                description.height = height + self.MARGIN
                self.root.text_size = pre_text_size
        else:
            if self.id in counters:
                del counters[self.id]

    def draw(self):
        Box.draw(self)
        if self.is_active:
            # If cursor in zone, make another rectangle with brighter color
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            tris_verts, tris_indices = make_box(self.origin, self.width - 2, self.height - 2, pattern='TRIS',
                                                bevel_radius=self.bevel_radius, bevel_segments=self.bevel_segments, origin_point=self.origin_point)
            shader.uniform_float("color", (0.329 + .1, 0.329 + .1, 0.329 + .1, 1))
            box = batch_for_shader(shader, 'TRIS', {'pos': tris_verts}, indices=tris_indices)
            box.draw(shader)
