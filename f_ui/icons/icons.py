from pathlib import Path
import bpy
from bpy.app.handlers import persistent, load_post
import gpu


icons = {}
# Icons Source: https://ui.blender.org/icons


@persistent
def load_icons(_):
    for img_path in Path(__file__).parent.rglob("*.png"):
        img = bpy.data.images.load(str(img_path))
        icons[img_path.stem.removeprefix("blender_icon_").upper()] = gpu.texture.from_image(img)
        bpy.data.images.remove(img)


def register():
    load_post.append(load_icons)


def unregister():
    load_post.remove(load_icons)