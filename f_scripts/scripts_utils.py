from inspect import getsourcelines
from bpy.types import UILayout


class ScriptAppendablePie:
    subclasses = {}

    def __init_subclass__(cls):
        """
        When this class is subclassed by a pie class, parse its draw function and look for occupied directions.

        Even if it's:

            if (some_context_based_condition):
                pie.left(...)

        it should still count as occupied as long as there's a possibility that it will be called.
        This parse is very basic but it should be fine.

        """
        # TODO: Permanently add script to pie and also be able to remove it. Any specific case scripts that are only used at a certain time in the workflow... 
        # ...can be added as needed and removed afterwards.

        ScriptAppendablePie.subclasses[cls.__name__] = cls
        cls.direction_occupant = {"left": None, "right": None, "bottom": None, "top": None, "top_left": None, "top_right": None, "bottom_left": None, "bottom_right": None}

        for line in getsourcelines(cls.draw)[0]:
            line = line.strip()
            if line.startswith('#'):
                continue
            if not line.startswith("pie."):
                continue
            if (direction := line[len("pie."):line.index('(')]) in cls.direction_occupant:
                cls.direction_occupant[direction] = True

    @property
    def pie_wrapper(self):
        def wrapper(layout: UILayout):
            from ..a_utils.utils_bl_ui import PieWrapper
            return PieWrapper(self.__class__, layout)
        return wrapper
