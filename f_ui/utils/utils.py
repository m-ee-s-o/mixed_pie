from bpy.types import Event
from mathutils import Vector
from time import time


class Attr_Holder:
    def __init__(self):
        """ Since UI elements are instantiated every tick, store persisting attr here. """
        self.hold = False     # Will be set by elements with hold like resizer and scroll bar.
                              # Will be checked by element that has hover effects. If true, don't do effect.
        self.drag = ("", "")  # Will be used by elements with drag-toggle function like prop

        # Event attributes
        self._initial_press_key_location = None
        self._last_press = Vector((0, 0))
        self._custom_type = None
        self._last_press_time = 0
        self.parse_dragmove_immediately_regardless_of_distance = False
        self.disruptor = {'ESC'}


class EventTypeIntercepter:
    def __init__(self, event: Event, ui_scale, attr_holder):
        self._event = event
        self.handled = None
        self.ui_scale = ui_scale
        self.attr_holder = attr_holder
        self.cursor = Vector((event.mouse_region_x, event.mouse_region_y))
        self._custom_value = None

        if event.type in attr_holder.disruptor and event.value == 'PRESS':
            attr_holder._custom_type = None
            attr_holder._initial_press_key_location = None
            self.set_mouse_press_release('RELEASE')
            if event.type != 'ESC':
                attr_holder.disruptor.remove(event.type)
            return

        if not (event.type.startswith("MOUSE") or event.type.endswith("MOUSE")):
            return

        if event.type == 'MOUSEMOVE' and attr_holder._initial_press_key_location  \
                and ((self.cursor - attr_holder._initial_press_key_location[1]).magnitude >= 10 * ui_scale
                     or attr_holder.parse_dragmove_immediately_regardless_of_distance):
            attr_holder._custom_type = 'DRAGMOVE'

        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE'}:
            if attr_holder._initial_press_key_location and (event.value != 'RELEASE' or attr_holder._initial_press_key_location[0] != event.type):
                # If you've clicked and haven't released, any other click won't revert values...
                # ...(useful for not cancelling dragmove when buttons other than the disruptors are clicked)
                return
            self.set_mouse_press_release(event.value)
    
    def set_mouse_press_release(self, value, key=""):
        match value:
            case 'PRESS':
                current = time()
                if current - self.attr_holder._last_press_time <= 1:
                    if (self.cursor - self.attr_holder._last_press).magnitude <= 10 * self.ui_scale:
                        self._custom_value = 'DOUBLECLICK'

                self.attr_holder._last_press_time = current
                self.attr_holder._last_press = self.cursor
                self.attr_holder._initial_press_key_location = (key or self._event.type, self.cursor)

            case 'RELEASE':
                if self.attr_holder._custom_type == 'DRAGMOVE':
                    self._custom_value = 'DRAGRELEASE'
                    self.attr_holder._custom_type = None

                self.attr_holder._initial_press_key_location = None

    def __getattribute__(self, __name):
        match __name:
            case "type" if (custom := super().__getattribute__("attr_holder")._custom_type):
                return custom
            case "value" if (custom := super().__getattribute__("_custom_value")):
                return custom
            case "set_mouse_press_release":
                return super().__getattribute__(__name)
            case _ if __name in super().__getattribute__("__dict__"):
                return super().__getattribute__(__name)
            case _:
                return getattr(super().__getattribute__("_event"), __name)
