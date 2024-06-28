from math import degrees, radians
from mathutils import Matrix, Vector
from .ui_base_layout import Layout
from .ui_button import PieButton
from ..utils.utils_circle import Circle


class PieMenuLayout(Layout):
    class Buttons(list):
        _hash_table = {}

        def append(self, button: PieButton):
            self._hash_table[button.id] = button
            super().append(button)

        def __getitem__(self, index):
            if isinstance(index, str):  # When id is passed instead
                return self._hash_table[index]
            return super().__getitem__(index)

    def __init__(self, operator, origin):
        self.DEV_DPI = 72
        super().__init__(operator, origin)
        self.MARGIN = 10 * self.ui_scale
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))

        self.text_size = 14
        self.buttons = self.Buttons()
        self.cursor_angle = 0

        self.STARTING_ZONE_RADIUS = 12 * self.ui_scale
        self.CENTER_CIRCLE_THICKNESS = 8 * self.ui_scale
        self.ARROW_HEAD_LENGTH = 40 * self.ui_scale

        self.PIE_RADIUS = 100 * self.ui_scale

    def call_modals(self, context, event):
        self.norm_cursor_loc = event.cursor - self.origin
        if (self.norm_cursor_loc.magnitude >= self.STARTING_ZONE_RADIUS):
            self.cursor_angle = degrees(self.norm_cursor_loc.angle_signed(Vector((10, 0))))
            zone_angle = 360 / len(self.buttons)
            offset = zone_angle / 2
            for i in range(len(self.buttons)):
                if (i != 0) and (self.cursor_angle < 0):
                    self.cursor_angle += 360
                if (zone_angle * i - offset) < self.cursor_angle < (zone_angle * (i + 1) - offset):
                    self.buttons[i].active = True
                    break
        
        increment = 360 / len(self.buttons)
        for i, button in enumerate(self.buttons):
            button.angle = increment * i
            button.origin = Vector((self.PIE_RADIUS, 0))
            button.origin.rotate(Matrix.Rotation(radians(button.angle), 2))
            button.origin += self.origin
            # label uses origin point at top left, button's is at center so offset
            button.button_label.origin = button.origin + Vector((-button.button_label.width / 2, button.button_label.height / 2))        

        super().call_modals(context, event)
    
    def draw(self):
        self.draw_center_ui()
        if hasattr(self, "button_groups"):
            self.draw_button_groups()
        super().draw()

    def draw_center_ui(self):
        Circle.draw(self.origin, self.STARTING_ZONE_RADIUS, self.CENTER_CIRCLE_THICKNESS, color=(0.329, 0.329, 0.329, 1))
        Circle.draw(self.origin, self.STARTING_ZONE_RADIUS + 1, self.CENTER_CIRCLE_THICKNESS - 2, color=(0, 0, 0, 1))

        if self.norm_cursor_loc.magnitude >= self.STARTING_ZONE_RADIUS:
            Circle.draw(self.origin, self.STARTING_ZONE_RADIUS + 2, self.CENTER_CIRCLE_THICKNESS - 4,
                        color=(0.278, 0.447, 0.702, 1), arc=60, offset_angle=self.cursor_angle + 30)

    def draw_button_groups(self):
        for group in self.button_groups:
            arc = 0
            for current_id, next_id in zip(group, group[1:]):
                current = self.buttons[current_id]
                current_angle = current.angle
                next = self.buttons[next_id]
                next_angle = next.angle
                if current_angle > next_angle:
                    arc += next_angle - current_angle
                else:
                    arc += 360 - (current_angle - next_angle)

            Circle.draw(self.origin, self.PIE_RADIUS, arc=arc % 360, offset_angle=self.buttons[group[-1]].angle, style='LINE')

    def button(self, id, label="", descriptor=None):
        button = PieButton(self, id, label, descriptor)
        self.buttons.append(button)
        return button
