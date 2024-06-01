bl_info = {
    "name": "Mixed Pie",
    "author": "m1Izu",
    "version": (0, 0, 0),
    "blender": (3, 5, 0),
    "location": "",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Interface",
}


from pathlib import Path
import importlib


modules = {
    'first': [],
    'prop': [],
    'else': [],
    'last': [],
}

# print("----------------------------------------------------------------", Path.cwd())
# print("----------------------------------------------------------------", __file__)
# print(Path(__file__).parent)
# print(__path__)

for path in Path(__file__).parent.rglob("*.py"):   
    path_parts = path.parts
    if not path_parts[-1].startswith("__"):
        n = path_parts.index(__package__)
        module = ".".join(path_parts[n:]).removesuffix(".py")
        key = ('first' if module.endswith(("_prop", "init")) else
               'prop' if module == ("prop") else
               'last' if module.endswith("out") else
               'else')
        modules[key].append(importlib.import_module(module))


if "bpy" in locals():
    for group in modules.values():
        for module in group:
            if module.__name__.endswith("icons.icons"):
                continue
            importlib.reload(module)
else:
    import bpy


def register():
    for group in modules.values():
        for module in group:
            if hasattr(module, "register"):
                module.register()


def unregister():
    for group in modules.values():
        for module in group:
            if hasattr(module, "unregister"):
                module.unregister()


if __name__ == "__main__":
    register()
