import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ..utils.utils_box import make_box, point_inside
from .ui_panel_layout import PanelLayout


class Bounds:
    @property
    def top(self): return self.origin.y
    @property
    def bottom(self): return self.origin.y - self.height
    @property
    def left(self): return self.origin.x
    @property
    def right(self): return self.origin.x + self.width
    @property
    def top_left(self): return self.origin.copy()
    @property
    def top_right(self): return Vector((self.right, self.top))
    @property
    def bottom_left(self): return Vector((self.left, self.bottom))
    @property
    def bottom_right(self): return Vector((self.right, self.bottom))


class Box(Bounds):
    point_inside = point_inside
    inherit = PanelLayout.inherit
    center = PanelLayout.center
    icon = PanelLayout.icon
    label = PanelLayout.label
    recur_offset_children_origin = PanelLayout.recur_offset_children_origin

    def __init__(self, parent, width, height, fill=True, color=(1, 1, 1, 1)):
        self.inherit(parent)
        self.width = width
        self.height = height
        self.children = []
        self.color = color
        self.fill = fill
        self.skip_bevel = set()
        self.bevel_radius = self.root.bevel_radius * self.ui_scale
        self.bevel_segments = self.root.bevel_segments * self.ui_scale
        self.origin_point = 'TOP_LEFT'

    def make(self):
        bevel = {'bevel_radius': self.bevel_radius, 'bevel_segments': self.bevel_segments}
        if self.fill:
            self.draw_vertices, self.draw_indices = make_box(self.origin, self.width, self.height, pattern='TRIS',
                                                             **bevel, origin_point=self.origin_point, skip_bevel=self.skip_bevel)
        else:
            self.draw_vertices = make_box(self.origin, self.width, self.height, **bevel, origin_point=self.origin_point, skip_bevel=self.skip_bevel)

    def draw(self):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", self.color)

        if self.fill:
            box = batch_for_shader(shader, 'TRIS', {'pos': self.draw_vertices}, indices=self.draw_indices)
        else:
            box = batch_for_shader(shader, 'LINES', {'pos': self.draw_vertices})

        box.draw(shader)

    def snap_to(self, target, side_of_target):
        pre_origin = self.origin
        match side_of_target:
            case 'LEFT':
                self.origin = target.origin.copy()
                self.origin.x -= self.width + 1
                target.skip_bevel = {'TOP_LEFT', 'BOTTOM_LEFT'}
                self.skip_bevel = {'TOP_RIGHT', 'BOTTOM_RIGHT'}
            case 'RIGHT':
                self.origin = target.origin.copy()
                self.origin.x += target.width + 1
                target.skip_bevel = {'TOP_RIGHT', 'BOTTOM_RIGHT'}
                self.skip_bevel = {'TOP_LEFT', 'BOTTOM_LEFT'}
            case 'TOP':
                self.origin = target.origin.copy()
                self.origin.y += self.height + 1
                target.skip_bevel = {'TOP_LEFT', 'TOP_RIGHT'}
                self.skip_bevel = {'BOTTOM_LEFT', 'BOTTOM_RIGHT'}
            case 'BOTTOM':
                self.origin = target.origin.copy()
                self.origin.y -= target.height + 1
                target.skip_bevel = {'BOTTOM_LEFT', 'BOTTOM_RIGHT'}
                self.skip_bevel = {'TOP_LEFT', 'TOP_RIGHT'}
        self.root.recur_offset_children_origin(self, *(self.origin - pre_origin))
