from mathutils import Vector
import blf
from .ui_panel_layout import PanelLayout
from .ui_box import Box


class LabelBox:
    inherit = PanelLayout.inherit

    def __init__(self, parent, text):
        self.adjustable = True
        self.text = str(text)
        Box.__init__(self, parent, 0, 0, fill=False)
        self.text_size = self.root.text_size
        self.alignment = self.root.text_alignment

        # Set minimum size
        blf.size(0, self.text_size * self.ui_scale)
        # self.height = blf.dimensions(0, ")")[1]
        self.height = blf.dimensions(0, self.text)[1]
        self.width = blf.dimensions(0, self.text)[0]

    def make(self):
        self.label_dimensions = self.get_label_dimensions(self.text)
        if not self.adjustable:
            self.width = self.label_dimensions.x

        if self.parent.height < self.label_dimensions.y:
            raise Exception("Height not enough for text.")
        PanelLayout.center(self, x=getattr(self, "center_x", False), y=getattr(self, "center_y", False))
        # self.bevel_radius = 0
        # Box.make(self)

    def get_label_dimensions(self, text):
        blf.size(0, self.text_size * self.ui_scale)  # Needs to be here since it clashes with addons like Screencast Keys (blf.size is called very much)
        return Vector(blf.dimensions(0, text))

    def draw(self):
        # Box.draw(self)
        origin = self.origin.copy()
        origin.y -= self.height  # Origin of self (element) is at top left, blf's is at bottom left
        text = self.text

        # Check if text fits, and if it is not, truncate
        if self.label_dimensions.x > self.width:
            for i in range(len(self.text), 0, -1):
                text = self.text[0:i] + "..."
                if self.get_label_dimensions(text).x <= self.width:
                    break
            else:
                text = ""

        if self.alignment == 'CENTER':
            origin.x += (self.width / 2) - (self.get_label_dimensions(text).x / 2)
        # print(self.text)
        blf.position(0, *origin, 0)
        blf.size(0, self.text_size * self.ui_scale)
        # TODO: Parse color
        blf.draw(0, text)
