from mathutils import Vector


class Attr_Holder:
    """ Since UI elements are instantiated every tick, store persisting attr here. """
    hold = False  # Will be set by elements with hold like resizer and scroll bar.
                    # Will be checked by element that has hover effects. If true, don't do effect.
    drag = ("", "")  # Will be used by elements with drag-toggle function like prop


class EventTypeIntercepter:
    """ Used with layout.draw_again """
    def __init__(self, event):
        self._event = event
        self.handled = None
        self.cursor = Vector((event.mouse_region_x, event.mouse_region_y))

    def __getattribute__(self, __name):
        if __name == "type" and super().__getattribute__("handled"):
                return None
        elif __name in {"handled", "cursor"}:
            return super().__getattribute__(__name)
        else:
            return getattr(super().__getattribute__("_event"), __name)
