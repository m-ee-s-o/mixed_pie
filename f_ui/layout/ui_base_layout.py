import bpy
from mathutils import Vector


class Layout:
    DEFAULT_BEVEL_RADIUS = 8
    DEFAULT_BEVEL_SEGMENTS = 5
    text_size = 21

    class Flow:
        def __init__(self):
            self.horizontal = False
            self.vertical = False

        def __call__(self, horizontal=False, vertical=False):
            if horizontal:
                self.horizontal = True
                self.vertical = False
            else:
                self.vertical = True
                self.horizontal = False

    def __init__(self, operator, origin):
        self.parent_modal_operator = operator
        self.origin = origin
        self.attr_holder = getattr(operator, "attr_holder", None)
        self.operator_context = 'INVOKE_DEFAULT'

        self.root = self
        self.flow = self.Flow()

        self.elements = []
        self.children = []
        self.draw_again = False
        self.hold = None

        self.bevel_radius = self.DEFAULT_BEVEL_RADIUS
        self.bevel_segments = self.DEFAULT_BEVEL_SEGMENTS

        self.ui_scale = (bpy.context.preferences.system.dpi / self.DEV_DPI)
        self.MARGIN = 20 * self.ui_scale
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))

    def call_modals(self, context, event):
        for element in reversed(self.elements):
            if event.handled:  # Make True once someone used the event
                break
            if hasattr(element, "modal"):
                element.modal(context, event)

    def make_elements(self):
        for element in self.elements:
            if hasattr(element, "make"):
                element.make()
    
    def draw(self):
        for element in self.elements:
            element.draw()

    def inherit(self, parent):
        for attr in {'root', 'attr_holder', 'ui_scale', 'MARGIN', 'vMARGIN_TOP_LEFT', 'parent_modal_operator'}:
            setattr(self, attr, getattr(parent, attr))

        self.parent = parent
        self.flow = self.root.Flow()
        self.flow(vertical=True)

        current_element = getattr(parent, "current_element", parent)

        if getattr(self, "no_spacing", False):
            self.origin = current_element.origin.copy()
        elif getattr(self, "custom_spacing", None) is not None:
            self.origin = current_element.origin.copy()
            if parent.children:
                if parent.flow.horizontal:
                    self.origin.x += current_element.width + self.custom_spacing
                else:
                    self.origin.y -= current_element.height + self.custom_spacing
            else:
                self.origin += parent.vMARGIN_TOP_LEFT
        else:
            if not parent.children:
                self.origin = parent.origin.copy()
                self.origin += parent.vMARGIN_TOP_LEFT
            else:
                if parent.flow.horizontal:
                    self.origin = Vector((current_element.origin.x + current_element.width + parent.MARGIN,
                                          current_element.origin.y))
                else:
                    self.origin = Vector((current_element.origin.x,
                                          current_element.origin.y - current_element.height - parent.MARGIN))

        parent.current_element = self
        parent.children.append(self)
        self.root.elements.append(self)