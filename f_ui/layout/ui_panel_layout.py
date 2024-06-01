from collections import defaultdict
import bpy
from mathutils import Vector
from ..utils.utils_box import make_box
from .ui_base_layout import Layout


# TODO: Tooltip


class PanelLayout(Layout):
    """
    Parent of all
    """

    def __init__(self, operator, origin):
        self.DEV_DPI = 144
        super().__init__(operator, origin)
        pre_margin = self.MARGIN
        pre_vMARGIN_TOP_LEFT = self.vMARGIN_TOP_LEFT

        self.MARGIN = 0
        self.vMARGIN_TOP_LEFT = Vector((0, 0))

        self.width, self.height = 500, 100
        self.main_box = self.box(self.width, self.height, color=(0, 0, 0, 1))
        self.elements.clear()
        self.children.clear()
        self.current_element = self

        self.MARGIN = pre_margin
        self.vMARGIN_TOP_LEFT = pre_vMARGIN_TOP_LEFT

    def main_box_modal(self, context, event):
        signature = "main_box_relocate_cursor"
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            # If there are other elements that's using .hold, return since it should be one at a time and when mouse is over two elements, only one works
            return
        relocate_cursor = getattr(self.attr_holder, "main_box_relocate_cursor", None)
        width = getattr(self.attr_holder, "main_box_previous_width", None)
        if not width:
            return

        if not relocate_cursor:
            # Top resize area
            _, corners = make_box(self.main_box.origin + Vector((0, self.MARGIN)), width, self.MARGIN * 2,
                                include_corners_copy=True, origin_point='TOP_LEFT')

            if Box.point_inside(None, event, corners):
                self.attr_holder.hold = signature
                context.window.cursor_modal_set('SCROLL_XY')
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.attr_holder.main_box_relocate_cursor = event.cursor
                    self.attr_holder.initial_cursor = self.parent_modal_operator.cursor.copy()
            elif self.attr_holder.hold == signature:
                # Since there are many elements that have this mechanism, put this condition so that wherever the mouse is, it would only execute this for one element
                context.window.cursor_modal_restore()
                self.attr_holder.hold = None

        if not relocate_cursor:
            return

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                self.attr_holder.main_box_relocate_cursor = None
                self.attr_holder.initial_cursor = None
                self.attr_holder.hold = None
            case 'ESC' if event.value == 'PRESS':
                self.parent_modal_operator.cursor = self.attr_holder.initial_cursor
                self.attr_holder.initial_cursor = None
                self.attr_holder.main_box_relocate_cursor = None
                event.handled = True
            case 'MOUSEMOVE':  # Put oustide of "if point_inside", since it can lag (e.g., executed when cursor is outside of area)
                current_cursor = event.cursor
                initial_cursor = relocate_cursor

                self.parent_modal_operator.cursor += current_cursor - initial_cursor
                self.attr_holder.main_box_relocate_cursor = current_cursor

                event.handled = True
                self.draw_again = True

    def call_modals(self, context, event):
        self.main_box_modal(context, event)
        super().call_modals(context, event)

    def make_elements(self):
        box = self.main_box
        if self.children:
            rightmost = max(self.children, key=lambda child: child.origin.x + child.width)
            box.width = rightmost.origin.x + rightmost.width + self.MARGIN - self.origin.x
            self.attr_holder.main_box_previous_width = box.width  # Used in self.main_box_modal

            bottommost = min(self.children, key=lambda child: child.origin.y - child.height)
            box.height = self.origin.y - bottommost.origin.y + bottommost.height + self.MARGIN

        box.make()
        super().make_elements()
    
    def draw(self):
        self.main_box.draw()
        super().draw()

    def adjust(self):
        children = self.children
        if len(children) == 1:
            if getattr(children[0], "adjustable", False):
                children[0].width = self.width - (self.MARGIN * 2)
            else:
                children[0].origin.x = self.origin.x + (self.width / 2) - (children[0].width / 2)
        elif len(children) > 1:
            left_margin = children[0].origin.x - self.origin.x  # If first child (basis) was offset, adjust accordingly
            space = self.width - left_margin - self.MARGIN
            adjustables = defaultdict(list)
            non_adjustables = defaultdict(list)
            child_groups = defaultdict(list)
            for child in children:
                if getattr(child, "adjustable", False):
                    adjustables[child.origin.x].append(child)
                else:
                    non_adjustables[child.origin.x].append(child)
                child_groups[child.origin.x].append(child)

            for child_group in non_adjustables.values():
                space -= max(child.width for child in child_group)

            remaining_space = space - (self.MARGIN * (len(child_groups) - 1))
            if adjustables:
                width_each = remaining_space / len(adjustables)

                for child_list in adjustables.values():
                    for child in child_list:
                        child.width = width_each

                child_groups = list(child_groups.values())
                for i, child_group in enumerate(child_groups):
                    if i != 0:
                        previous = child_groups[i - 1]
                        for child in child_group:
                            new_origin_x = previous[0].origin.x + max(child.width for child in previous) + self.MARGIN
                            offset = new_origin_x - child.origin.x
                            child.origin.x = new_origin_x
                            self.root.recur_offset_children_origin(child, offset_x=offset)

    def recur_offset_children_origin(self, parent, offset_x=0, offset_y=0):
        for child in parent.children:
            if offset_x:
                child.origin.x += offset_x
            if offset_y:
                child.origin.y += offset_y
            self.recur_offset_children_origin(child, offset_x, offset_y)

    def recur_get_all_children(self, parent, children=None):
        if children is None:
            children = []
        for child in parent.children:
            children.append(child)
            self.recur_get_all_children(child, children=children)
        return children

    def center(self, x=False, y=False):
        if x:
            self.origin.x = self.parent.origin.x + (self.parent.width / 2) - (self.width / 2)
        if y:
            self.origin.y = self.parent.origin.y - (self.parent.height / 2) + (self.height / 2)

    def box(self, width=0, height=0, fill=True, color=(1, 1, 1, 1)):
        if width == 0:
            width = 100 * self.ui_scale
        if height == 0:
            height = 100 * self.ui_scale
        return Box(self, width, height, fill=fill, color=color)

    def collection(self, id, collection, draw_item_func, property_group):
        return Collection(self, id, collection, draw_item_func, property_group)

    def label(self, text):
        return LabelBox(self, text)

    def text(self, data, property):
        return TextBox(self, data, property)

    def icon(self, id):
        return IconBox(self, id)

    def operator(self, id_name, label="", icon=None, emboss=True):
        return UI_Operator(self, id_name, label, icon, emboss)

    def prop(self, data, property, label="", icon=None, emboss=True):
        return Prop(self, data, property, label, icon, emboss)


def register():
    # Prevent circular import by importing the following after everything is done importing.
    # It doesn't matter if these are imported last since they're only needed at runtime at function scope
    global Box, LabelBox, TextBox, Collection, IconBox, UI_Operator, Prop
    from .ui_box import Box
    from .ui_label import LabelBox
    from .ui_text import TextBox
    from .collection.ui_collection import Collection
    from .ui_icon import IconBox
    from .ui_operator import UI_Operator
    from .ui_prop import Prop
