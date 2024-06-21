from collections import defaultdict
from pathlib import Path
import importlib
from inspect import getmembers, isclass


# Uncommonly used, paramterless, or very specific action will be added as "script" rather than have its own operator class


class Script:
    def __init__(self, cls):
        self.cls = cls
        self.name = getattr(cls, "name", None) or f"    - {cls.__name__.replace('_', ' ')}"

        doc = str(cls.__doc__)
        tooltip = ""
        # Remove space, period and newline if any at end of text
        for i in range(len(doc) - 1, -1, -1):
            if not tooltip and doc[i] in {' ', '.', '\n'}:
                continue
            tooltip = doc[:i + 1]
            break
        # Remove space and newline if any at the beginning of text
        temp = ""
        for i in range(len(tooltip)):
            if not temp and tooltip[i] in {' ', '\n'}:
                continue
            temp = tooltip[i:]
            tooltip = temp
            break
        # Remove extra spaces cause by indentation per line
        self.tooltip = '\n'.join(line.strip(' ') for line in tooltip.split('\n'))

    def __getattribute__(self, name):
        value = getattr(super().__getattribute__("cls"), name, None)
        return value if value is not None else super().__getattribute__(name)


script_categories = defaultdict(list)

for path in Path(__file__).parent.rglob("*.py"):   
    if not path.name.startswith("scriptss"):
        continue
    n = path.parts.index(__package__.partition('.')[0])
    module = ".".join(path.parts[n:]).removesuffix(".py")
    module = importlib.import_module(module)

    for class_name, cls in getmembers(module, isclass):
        if hasattr(cls, "invoke") or hasattr(cls, "execute"):
            script_categories[module.__name__.partition("scriptss_")[-1].replace('_', ' ').title()].append(Script(cls))
