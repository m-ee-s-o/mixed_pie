from math import radians
from mathutils import Matrix, Vector
from ..utils.utils import EventTypeIntercepter


def make_box(origin, width, height, pattern='LINE', bevel_radius=0, bevel_segments=4,
             origin_point='TOP_LEFT', skip_bevel:set=None, return_corners=False):
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

    corners = []
    point.y -= height; corners.append(point.copy())  # BottomLeft
    point.x += width; corners.append(point.copy())   # BottomRight
    point.y += height; corners.append(point.copy())  # TopRight
    point.x -= width; corners.append(point.copy())   # TopLeft 

    if bevel_radius < 1 or bevel_segments < 1:
        box_points.extend(corners)
    else:
        mat_rot = Matrix.Rotation(radians(90 / segments), 2)
        b_height = height - bevel_radius * 2
        b_width = width - bevel_radius * 2
        x_bevel = Vector((bevel_radius, 0))
        y_bevel = Vector((0, bevel_radius))

        if 'BOTTOM_LEFT' not in skip_bevel:
            point.y -= b_height + bevel_radius; box_points.append(point.copy())
            origin = point + x_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
            point += origin
        else:
            point.y -= height
            point.x += bevel_radius
            box_points.append(corners[0].copy())

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
            box_points.append(corners[1].copy())

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
            box_points.append(corners[2].copy())

        if 'TOP_LEFT' not in skip_bevel:
            point.x -= b_width; box_points.append(point.copy())
            origin = point - y_bevel
            point -= origin
            for _ in range(segments):
                point.rotate(mat_rot); box_points.append(point + origin)
        else:
            box_points.append(corners[3].copy())

    match origin_point:
        case 'CENTER':
            for point in (box_points if bevel_radius < 1 else (*corners, *box_points)):
                point.x -= width / 2
                point.y += height / 2

    ret = []

    if pattern == 'LINE':
        box_points = [point for point in box_points for _ in range(2)]
        box_points.append(box_points.pop(0))
        ret.append(box_points)
    else:
        half = len(box_points) // 2
        latter_half = box_points[half:]
        box_points = box_points[:half]
        box_points.extend(reversed(latter_half))
        ret.append(box_points)
        ret.append(get_tris_indices(box_points))

    if return_corners:
        ret.append(corners)

    return ret


def get_tris_indices(vertices, loop=False):
    tris_indices = []

    half = len(vertices) // 2
    for i in range(half - 1):
        tris_indices.append([i, i + 1, i + half])
        tris_indices.append([i + half, i + 1 + half, i + 1])

    if loop:
        i = half - 1
        tris_indices.append([i, 0, i + half])
        tris_indices.append([i + half, 0, i + 1])

    return tris_indices

def point_inside(self, point: EventTypeIntercepter | Vector, originWidthHeight: tuple[Vector|tuple, int, int] = None):
    if isinstance(point, Vector):
        pass
    elif isinstance(point, EventTypeIntercepter):
        point = point.cursor
    else:
        raise NotImplementedError

    if originWidthHeight:
        origin, width, height = originWidthHeight
        if origin[0] <= point.x <= origin[0] + width  \
                and origin[1] - height <= point.y <= origin[1]:
            return True
    else:
        if self.left <= point.x <= self.right  \
                and self.bottom <= point.y <= self.top:
            return True
