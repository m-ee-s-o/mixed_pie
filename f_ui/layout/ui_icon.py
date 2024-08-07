import gpu
from gpu_extras.batch import batch_for_shader
from .ui_box import Box
from ..icons.icons import icons, load_icons


class IconBox(Box):
    def __init__(self, parent, id):
        if not icons:
            load_icons("")

        self.texture = icons[id]
        width = self.texture.width
        height = self.texture.height
        if (scale := getattr(parent.root, "icon_scale", None)):
            scale = max(0.1, min(scale, 1))  # Clamp: 0.1 - 1
            width *= scale
            height *= scale
        Box.__init__(self, parent, width * parent.ui_scale, height * parent.ui_scale, False)
        self.bevel_radius = 0

    def draw(self):
        Box.center(self, y=True)
        # self.make()
        # Box.draw(self)

        shader = gpu.shader.from_builtin('IMAGE_COLOR')

        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {
                "pos": (self.bottom_left, self.bottom_right, self.top_right, self.top_left),
                # Trim above and below since there seems to be a line at the side
                # "texCoord": ((0, 0.02), (0.99, 0.02), (0.99, 0.98), (0, 0.98)),
                "texCoord": ((0, 0), (0.99, 0), (0.99, 1), (0, 1)),
                # "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
            },
        )
        shader.bind()
        shader.uniform_sampler("image", self.texture)
        shader.uniform_float("color", (0.5, 0.5, 0.5, 1) if not self.active else (1, 1, 1, 1))

        gpu.state.blend_set("ALPHA")
        batch.draw(shader)
        gpu.state.blend_set("NONE")
