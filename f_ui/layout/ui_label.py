# import re
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
        self.text_size = self.root.text_size * self.ui_scale
        self.is_center_aligned = self.root.text_alignment.center
        self.label_color = (1, 1, 1, 1)

        # Set minimum size
        blf.size(0, self.text_size)
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
        blf.size(0, self.text_size)  # Needs to be here since it clashes with addons like Screencast Keys (blf.size is called very much)
        return Vector(blf.dimensions(0, text))

    def draw(self):
        # Box.draw(self)
        origin = self.origin.copy()
        origin.y -= self.height  # Origin of self (element) is at top left, blf's is at bottom left
        text = self.text
        if self.height > self.label_dimensions.y:
            origin.y += (self.height / 2) - (self.label_dimensions.y / 2)

        # Check if text fits, and if it is not, truncate
        if self.label_dimensions.x > self.width:
            for i in range(len(self.text), 0, -1):
                text = self.text[0:i] + "..."
                if self.get_label_dimensions(text).x <= self.width:
                    break
            else:
                text = ""

        if self.center:
            origin.x += (self.width / 2) - (self.get_label_dimensions(text).x / 2)

        # print(self.text)
        blf.position(0, *origin, 0)
        blf.size(0, self.text_size)

        # # TODO: Parse color
        # re.findall("<1, 1, 1, 1>")
        # code = "<c"
        # while True:
        #     if (index := text.find(code)) == -1:
        #         break
        #     if code == "<c":
        #         if (close_index := text.find(">", index + 2)
        #         code = "</c>"
        #     text.find()

        if self.active:
            if self.label_color != (1, 1, 1, 1):
                blf.color(0, *self.label_color)
                blf.draw(0, text)
                blf.color(0, 1, 1, 1, 1)        
            else:
                blf.draw(0, text)       
        else:
            blf.color(0, self.label_color[0] * 0.5, self.label_color[1] * 0.5, self.label_color[2] * 0.5, self.label_color[3])
            blf.draw(0, text)
            blf.color(0, 1, 1, 1, 1)       
