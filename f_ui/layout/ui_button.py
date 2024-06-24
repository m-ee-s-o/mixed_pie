import time
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ..utils.utils_box import make_box
from .ui_box import Box


counters = {}


class PieButton(Box):
    def __init__(self, parent, id, label, desciptor):
        super().__init__(parent, 0, 0, color=(0, 0, 0, 1))
        self.active = False
        self.id = id
        self.button_label = self.label(label)
        self.height = self.button_label.height + self.MARGIN * 2
        self.width = self.height
        self.origin_point = 'CENTER'
        pre_text_size = self.root.text_size
        self.description_text = desciptor(self) if desciptor else "None"
        self.text_size = self.root.text_size
        self.root.text_size = pre_text_size

    def modal(self, context, event):
        if self.active:
            if self.id not in counters:
                counters[self.id] = time.time()
            elif time.time() - counters[self.id] >= 0.75:
            # else:
                pre_text_size = self.root.text_size
                self.root.text_size = self.text_size
                dimensions = blf.dimensions(0, self.description_text)
                # dimensions = blf.dimensions(0, str(time.time() - counters[self.id]))
                description = Box(self, dimensions[0], dimensions[1], color=(0, 0, 0, 1))
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
        super().draw()
        if self.active:
            # If cursor in zone, make another rectangle with brighter color
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            tris_verts, tris_indices = make_box(self.origin, self.width - 2, self.height - 2, pattern='TRIS',
                                                bevel_radius=self.bevel_radius, bevel_segments=self.bevel_segments, origin_point=self.origin_point)
            shader.uniform_float("color", (0.329 + .1, 0.329 + .1, 0.329 + .1, 1))
            box = batch_for_shader(shader, 'TRIS', {'pos': tris_verts}, indices=tris_indices)
            box.draw(shader)
