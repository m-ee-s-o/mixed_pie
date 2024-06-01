from math import radians
from mathutils import Matrix, Vector
import gpu
from gpu_extras.batch import batch_for_shader
from .utils_box import get_tris_indices


class Circle:
    @classmethod
    def create(cls, origin, radius, arc, offset_angle):
        vertices = []
        mat_rot = Matrix.Rotation(radians(1), 2)

        init_point = Vector((radius, 0))
        if offset_angle:
            init_point.rotate(Matrix.Rotation(radians(offset_angle), 2))
        vertices.append(init_point + origin)

        point = init_point
        for _ in range(1, int(arc)):
            point = point @ mat_rot
            vertices.append(point + origin)

        return vertices

    @classmethod
    def draw(cls, origin, radius, thickness=0, color=(1, 1, 1, 1), arc=360, offset_angle=0, style='TRIS', force_loop=False):
        inner = cls.create(origin, radius, arc, offset_angle)
        outer = cls.create(origin, radius + thickness, arc, offset_angle) if thickness > 1 else []
        vertices = inner + outer

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", color)

        match style:
            case 'TRIS':
                indices = get_tris_indices(vertices, loop=(arc >= 360) or force_loop)
                circle = batch_for_shader(shader, 'TRIS', {'pos': vertices}, indices=indices)
                circle.draw(shader)

            case 'LINE':
                vertices = [vertex for vertex in vertices for _ in range(2)]
                if (arc >= 360) or force_loop:
                    vertices.append(vertices.pop(0))
                else:
                    vertices = vertices[1:-1]
                circle = batch_for_shader(shader, 'LINES', {'pos': vertices})
                gpu.state.line_width_set(2)
                circle.draw(shader)
                gpu.state.line_width_set(1)
