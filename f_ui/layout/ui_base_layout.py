import bpy
from mathutils import Vector


class Layout:
    DEFAULT_BEVEL_RADIUS = 6
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
    
    class TextAlignment:
        options = {"left", "center", "right"}

        def __init__(self):
            super().__setattr__("left", True)
            super().__setattr__("center", False)
            super().__setattr__("right", False)

        def __setattr__(self, name, value):
            if name in self.options:
                for option in self.options:
                    if option == name:
                        continue
                    super().__setattr__(option, False)
            elif name != "active":
                raise NotImplementedError
            if value:
                super().__setattr__(name, value)
            else:
                super().__setattr__("left", True)  # Make left at least True

        @property
        def active(self):
            for option in self.options:
                if getattr(self, option):
                    return option.upper()
        
        @active.setter
        def active(self, value_in_caps):
            setattr(self, value_in_caps.lower(), True)

    class ChangeTemporarily:
        # Note: If this doesn't affect performance much, it's fine

        def __init__(self, parent, attr, value):
            self.parent = parent
            self.attr = attr
            self.pre_value = getattr(parent, attr)
            setattr(parent, attr, value)

        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, exc_traceback):
            setattr(self.parent, self.attr, self.pre_value)

    def __init__(self, operator, origin):
        self.parent_modal_operator = operator
        self.origin = origin
        self.attr_holder = getattr(operator, "attr_holder", None)
        self.operator_context = 'INVOKE_DEFAULT'

        self.root = self
        self.flow = self.Flow()
        self.text_alignment = self.TextAlignment()

        self.elements = []
        self.children = []
        self.reinitialize = False
        self.active = True

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
        for attr in {'root', 'attr_holder', 'ui_scale', 'MARGIN', 'vMARGIN_TOP_LEFT', 'parent_modal_operator', 'active'}:
            setattr(self, attr, getattr(parent, attr))

        self.parent = parent
        self.flow = self.root.Flow()
        self.flow(vertical=True)

        current_element = getattr(parent, "current_element", parent)

        if (origin_of_next_child := getattr(parent, "origin_of_next_child", None)):
            self.origin = origin_of_next_child
            parent.origin_of_next_child = None

        elif (custom_spacing := getattr(parent, "custom_spacing_between_children", None)) is not None:
            if current_element != parent:
                self.origin = current_element.origin.copy()
                if parent.flow.horizontal:
                    self.origin.x += current_element.width + custom_spacing
                else:
                    self.origin.y -= current_element.height + custom_spacing
            else:
                self.origin = current_element.origin + self.vMARGIN_TOP_LEFT

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
