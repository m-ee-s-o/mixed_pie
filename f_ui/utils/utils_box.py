from math import radians
from bpy.types import Event
from mathutils import Matrix, Vector
from ..utils.utils import EventTypeIntercepter


class Corners(list):
    corners_index = {'bottom_left': 0,
                     'bottom_right': 1,
                     'top_right': 2,
                     'top_left': 3}

    def __init__(self, point, width, height):
        c_point = point.copy()
        c_point.y -= height / 2; self.append(c_point.copy())  # BottomLeft
        c_point.x += width; self.append(c_point.copy())       # BottomRight
        c_point.y += height; self.append(c_point.copy())      # TopRight
        c_point.x -= width; self.append(c_point.copy())       # TopLeft 

    def __getattribute__(self, __name):
        if __name in (indices := super().__getattribute__("corners_index")):
            return self[indices[__name]]
        else:
            return super().__getattribute__(__name)


def make_box(origin, width, height, pattern='LINE', bevel_radius=0, bevel_segments=4,
             include_corners_copy=False, origin_point='CENTER', skip_bevel=None):
    """
    Returns a list of vertices that is ready to be drawn.

    if pattern == 'LINE'
        returns [draw_vertices]
    else (e.g., 'TRIS')
        returns [draw_vertices, draw_indices]

    if include_corners_copy -> returns.append(box_corners)
    """
    segments = int(bevel_segments)
    box_points = []
    point = Vector(origin)
    skip_bevel = skip_bevel or set()

    # MiddleLeft
    point.x -= width / 2

    corners = Corners(point, width, height)

    if bevel_radius < 1 or bevel_segments < 1:
        box_points.extend(corners)
    else:
        mat_rot = Matrix.Rotation(radians(90 / segments), 2)
        b_height = height - bevel_radius * 2
        b_width = width - bevel_radius * 2
        x_bevel = Vector((bevel_radius, 0))
        y_bevel = Vector((0, bevel_radius))

        if 'BOTTOM_LEFT' not in skip_bevel:
            point.y -= b_height / 2; box_points.append(point.copy())
            origin = point + x_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
            point += origin
        else:
            point.y -= height / 2
            point.x += bevel_radius
            box_points.append(corners.bottom_left.copy())

        if 'BOTTOM_RIGHT' not in skip_bevel:
            point.x += b_width; box_points.append(point.copy())
            origin = point + y_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
            point += origin
        else:
            point.x += width - bevel_radius
            point.y += bevel_radius
            box_points.append(corners.bottom_right.copy())

        if 'TOP_RIGHT' not in skip_bevel:
            point.y += b_height; box_points.append(point.copy())
            origin = point - x_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
            point += origin
        else:
            point.y += height - bevel_radius
            point.x -= bevel_radius
            box_points.append(corners.top_right.copy())

        if 'TOP_LEFT' not in skip_bevel:
            point.x -= b_width; box_points.append(point.copy())
            origin = point - y_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
        else:
            box_points.append(corners.top_left.copy())

    match origin_point:
        case 'TOP_LEFT':
            for point in (box_points if bevel_radius < 1 else (*corners, *box_points)):
                point.x += width / 2
                point.y -= height / 2

    ret = []

    if pattern == 'LINE':
        box_points = [point for point in box_points for _ in range(2)]
        box_points.append(box_points.pop(0))
    else:
        half = len(box_points) // 2
        latter_half = box_points[half:]
        box_points = box_points[:half]
        box_points.extend(reversed(latter_half))
        ret.append(get_tris_indices(box_points))

    ret.insert(0, box_points)

    if include_corners_copy:
        ret.append(corners)

    return ret


def get_tris_indices(vertices, prior_tris_vertices: list=None, loop=False):
    tris_indices = []

    half = len(vertices) // 2
    for i in range(half - 1):
        tris_indices.append([i, i + 1, i + half])
        tris_indices.append([i + half, i + 1 + half, i + 1])

    if loop:
        i = half - 1
        tris_indices.append([i, 0, i + half])
        tris_indices.append([i + half, 0, i + 1])

    # # Offset to match the tris_indices to the indices of their verts
    # if prior_tris_vertices:
    #     len_prior_verts = len(prior_tris_vertices)
    #     for i in tris_indices:
    #         for j in range(3):
    #             i[j] += len_prior_verts

    return tris_indices

def point_inside(self, point: Event | Vector, corners: Corners=None):
    if isinstance(point, Vector):
        pass
    elif isinstance(point, (Event, EventTypeIntercepter)):
        event = point
        point = Vector((event.mouse_region_x, event.mouse_region_y))
    else:
        raise NotImplementedError

    corners = corners if corners else self.corners
    if corners.bottom_left.x <= point.x <= corners.bottom_right.x  \
            and corners.bottom_left.y <= point.y <= corners.top_left.y:
        return True

