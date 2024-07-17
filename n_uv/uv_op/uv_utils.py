
from collections import defaultdict
from typing import DefaultDict
from bpy.types import Operator
from bpy.props import BoolProperty, FloatVectorProperty
import bmesh
from mathutils import Vector


def get_center_uvs(uvs, also_return_bounds=False):
    x_s, y_s = [], []
    for uv in uvs:
        x_s.append(uv[0])
        y_s.append(uv[1])

    min_bounds = Vector((min(x_s), min(y_s)))
    max_bounds = Vector((max(x_s), max(y_s)))
    center = Vector(((max_bounds.x + min_bounds.x) / 2, (max_bounds.y + min_bounds.y) / 2))

    return (center, min_bounds, max_bounds) if also_return_bounds else center


def get_ordered_radial_loops_around_vertex(vertex):
    """ Carousel around vertex. """
    order = []
    current = vertex.link_loops[0]
    for _ in range(len(vertex.link_loops)):
        order.append(current)
        current = current.link_loop_radial_next.link_loop_next
    return order


class Base_UVOpsPoll:
    @classmethod
    def poll(cls, context):
        if context.area.ui_type != 'UV':
            return False
        cls.poll_message_set('"UV Sync Selection" is enabled. Disable to proceed.')
        return not context.scene.tool_settings.use_uv_select_sync


class SpaceBetweenIslands:
    def space_between_islands_set(self, value):
        self.value_space_between_islands = value
        self.is_space_between_islands_set = True

    def reset_space_between_islands_update(self, context):
        self.is_space_between_islands_set = False

    is_space_between_islands_set: BoolProperty()
    reset_space_between_islands: BoolProperty(name="", update=reset_space_between_islands_update,
                                      description="Recalculate space based on image size")
    value_space_between_islands: FloatVectorProperty(size=2)
    space_between_islands: FloatVectorProperty(name="", size=2, subtype='XYZ', get=lambda self: self.value_space_between_islands,
                                       set=space_between_islands_set, description="In px")

    def get_space_between_islands(self, context, uv_bounds=False):
        img = context.space_data.image
        img_size = img.size if img else (256, 256)
        offset = self.value_space_between_islands
        if not self.is_space_between_islands_set:
            # http://wiki.polycount.com/wiki/Edge_padding
            # https://blenderartists.org/t/island-margins-in-what-units-is-it/667242
            # For 256x256, there's 2px margin for each island and it would be 4px for the space between two islands (256 / 64 == 4)
            # As for the space between an island and uv_bounds, since that only one island only half is needed (256 / 128 == 2)
            offset[:] = Vector(img_size) / (64 if not uv_bounds else 128)
        return Vector(offset[i] / img_size[i] for i in range(2))


class Modal_Get_UV_UvVectors:
    def get_uv_uvVectors(self):
        self.uv_uvVectors = defaultdict(list)
        for data, indicesToLoops in self.objsData_indicesToLoops.items():
            uv_layer, bm_faces = get_uvLayer_bmFaces(data)
            indicesToLoops.get_uv_uvVectors(uv_layer, bm_faces, self.uv_uvVectors,
                                            include_validity_tester=self, embed_uvData=self)


class Base_IndicesToLoops:
    @staticmethod
    def getIndicesToLoop(loop):
        face = loop.face
        for index, f_loop in enumerate(face.loops):
            if f_loop is loop:
                return (face.index, index)
            
    def get_uv_uvVectors(self, uv_layer, bm_faces, uv_uvVectors=None, include_validity_tester=False,
                         embed_uvData=False, embed=False):
        uv_uvVectors = uv_uvVectors if uv_uvVectors is not None else defaultdict(list)
        set_uv_uvVectors(uv_layer, bm_faces, uv_uvVectors, self, include_validity_tester, embed_uvData)
        if embed:
            self.uv_uvVectors = uv_uvVectors
        else:
            return uv_uvVectors


class IndicesToLoops(Base_IndicesToLoops, defaultdict):
    """ {faceIndex, [faceLoopIndex,...],...} """
    def __init__(self, include_uvs=False):
        super().__init__(list)
        if include_uvs:
            self.uvs = set()

    def construct(self, loop, uv=None):
        if uv:
            self.uvs.add(uv)
        faceIndex, faceLoopIndex = self.getIndicesToLoop(loop)
        self[faceIndex].append(faceLoopIndex)


class SeriesIndicesToLoops(Base_IndicesToLoops, list):
    """

    [(faceIndex, (faceLoopIndex,)),...]
        - A list of loop address that follows their edge loop series order.

    """
    def items(self):
        return self

    def construct(self, loop):
        faceIndex, faceLoopIndex = self.getIndicesToLoop(loop)
        self.append((faceIndex, (faceLoopIndex,)))

    def bulk_construct(self, loops):
        for loop in loops:
            self.construct(loop)   


def get_uvLayer_bmFaces(obj_data):
    bm = bmesh.from_edit_mesh(obj_data)
    uv_layer = bm.loops.layers.uv.active
    bm_faces = bm.faces
    bm_faces.ensure_lookup_table()
    return (uv_layer, bm_faces)


def set_uv_uvVectors(uv_layer, bm_faces, uv_uvVectors: DefaultDict[tuple, list], indicesToLoops: IndicesToLoops,
                     include_validity_tester: Operator=False, embed_uvData: Operator=False):
    uvData = set()
    for faceIndex, faceLoopIndices in indicesToLoops.items():
        loops = bm_faces[faceIndex].loops
        for faceLoopIndex in faceLoopIndices:
            loop = loops[faceLoopIndex]
            uv_data = loop[uv_layer]
            uvData.add(uv_data)
            uv = uv_data.uv
            uv_uvVectors[tuple(uv)].append(uv)

    if include_validity_tester:  # For modal operators with undo inside
        include_validity_tester.validity_test_loop = loop
    if embed_uvData:
        embed_uvData.uv_data = uvData


class SearchUV:
    # TODO: Update docs
    @classmethod
    def return_for_the_func_below(cls, prev_loops, first_call, is_line):
        if not first_call:
            return (prev_loops, is_line)

        loops = list(prev_loops.keys())
        indicesToLoops = SeriesIndicesToLoops()
        indicesToLoops.bulk_construct(loops)
        return loops, indicesToLoops, is_line

    @classmethod
    def connected_in_line_or_not(cls, uv_layer, loop_m, uv_m, prev_loops=None, prev_uv=None,
                                  is_line=True, first_call=True, entered_2=False):
        if not prev_loops:
            prev_loops = {}

        counter = 0
        looped = False
        uv_adjacentLoop = {}
        for loop in loop_m.vert.link_loops:
            uv_data = loop[uv_layer]
            uv = tuple(uv_data.uv)
            if uv != uv_m:  # Ignore split loop
                continue

            prev_loops[loop] = None
            counter += 1

            for index, adjacent_loop in enumerate((loop.link_loop_next, loop.link_loop_prev)):
                uv_data = adjacent_loop[uv_layer]
                uv = tuple(uv_data.uv)
                if uv == prev_uv:  # Prevent from going back to previous
                    continue
                if adjacent_loop in prev_loops:
                    looped = True
                    continue

                uv_data = uv_data if (index == 1) else loop[uv_layer]
                # .select_edge is the selection state of the edge between current loop and the next loop counterclockwise
                # loop[uv_layer].select_edge is between loop and loop.link_loop_next (next loop counterclockwise)
                if uv_data.select_edge:                    # For it to work for edge select mode
                    uv_adjacentLoop[uv] = adjacent_loop  # Gets only one loop in a uv location

        if (len_ := len(uv_adjacentLoop)):
            if len_ != 1:
                is_line = False
                # is_line will decide what distribute pattern to use. It will be True if a selection group is a two-endpoint line
                # If True, loops are distributed along that line straightly, else they'll be distributed based on their location

            if (len_ == 2) and first_call:
                entered_2 = True
                is_line = True

            for uv, loop in uv_adjacentLoop.items():
                if not is_line and (loop in prev_loops):
                    # If loop got included in the previous for-loop, ignore it
                    continue
                ignore_endpoint = False
                # If entered_2, it is checked if it's still a line or not
                # If line, the loops inbetween the endpoints will be added to loops_done,...
                # ...so that it is guaranteed that the search will start at one of the endpoints next time

                prev_loops, _is_line = cls.connected_in_line_or_not(uv_layer, loop, uv, prev_loops=prev_loops, prev_uv=uv_m,
                                                                     is_line=is_line, first_call=False, entered_2=entered_2)
                if is_line and not _is_line:  # is_line shouldn't be changed back to True once it's not True
                    is_line = _is_line
                if ignore_endpoint and (_is_line != "ignore endpoint"):
                    # If endpoint was already ignored in one side and the other side has multiple endpoints...
                    # ...thus making _is_line false, return the loops on the former side, ignore the latter
                    break
                if _is_line == "ignore endpoint":
                    ignore_endpoint = True

            if ignore_endpoint:  # Must be outside of for-loop; is_line still needs to be True for all iterations
                is_line = None

            return cls.return_for_the_func_below(prev_loops, first_call, is_line)
        else:
            if entered_2 and is_line:
                if looped:
                    is_line = False
                else:
                    # If started at middle of line, ignore last endpoint (remove last loop group)
                    for _ in range(counter):
                        prev_loops.popitem()
                    is_line = "ignore endpoint"

            return cls.return_for_the_func_below(prev_loops, first_call, is_line)

    @staticmethod
    def connected_in_same_island(uv_layer, loop_m, uv_m, active_only=False, get_uv_uvVector=False,
                                 include_uvs=False, active_uvs=None, loops_done=None):
        """
        Given a "loop_m", search every other loops in the same island.

        Parameters
            - active_only --- If true, only checks for the active uvs in an island.
            - get_uvVectors --- Get uvVector instead of indices_to_loop (loop "address").
            - include_uvs --- If get_uvVectors is False, include uvs as indicesToLoops.uvs.
            - active_uvs --- If supplied, when there is an active loop whose uv isn't in "active_uvs",
                              Returns.update({'ignore_island': None}).
            - loops_done --- If supplied, when there is a loop that is in "loops_done",
                              Returns.update({'ignore_island': None}).

        Returns
            - (loops, {(u, v): [(loop.face.index, loop_index_in_face_loops), ...})
                - loops contains all loops that these uv_vectors belong to; Add these to a "loops_done".
        """

        loops = {}
        current_loops = {v_loop: uv_m for v_loop in loop_m.vert.link_loops if (tuple(v_loop[uv_layer].uv) == uv_m)}

        while True:
            loops.update(current_loops)

            adjacent_loops = {}
            for loop in current_loops:
                for index, adjacent_loop in enumerate((loop.link_loop_next, loop.link_loop_prev)):
                    uv_data = adjacent_loop[uv_layer]
                    uv = tuple(uv_data.uv)
                    if adjacent_loop in loops:
                        continue

                    if active_only:
                        uv_data = uv_data if (index == 1) else loop[uv_layer]
                        if not uv_data.select_edge:
                            continue

                    adjacent_loops.update({
                        v_loop: uv for v_loop in adjacent_loop.vert.link_loops if (tuple(v_loop[uv_layer].uv) == uv)
                    })

            if adjacent_loops:
                current_loops = adjacent_loops
            else:
                ignore = False
                if get_uv_uvVector:
                    ret = uv_uvVector = defaultdict(list)
                    for loop, uv in loops.items():
                        uv_data = loop[uv_layer]
                        uvVector = uv_data.uv
                        if uv_data.select and (active_uvs and (uv not in active_uvs)) or loops_done and (loop in loops_done):
                            ignore = True
                        uv_uvVector[uv].append(uvVector)
                else:
                    ret = indicesToLoops = IndicesToLoops(include_uvs=include_uvs)
                    for loop, uv in loops.items():
                        if loop[uv_layer].select and (active_uvs and (uv not in active_uvs)) or loops_done and (loop in loops_done):
                            ignore = True
                        indicesToLoops.construct(loop, uv) if include_uvs else indicesToLoops.construct(loop)

                if ignore:
                    ret['ignore_island'] = None
                return loops, ret

    @classmethod
    def connected_in_same_active_edge_loop(cls, uv_layer, loop_m, uv_m):
        """
        Starting from a "loop_m" which is part of an edge loop, search for every other loops in that edge loop in order.

        Returns:
            - (loop_uv, looped)
                - loop_uv: {loop: uv,...} --- A dict of loop: uv ordered by edge loop connection.
                - looped: bool --- If edge loop looped (i.e., first element is connected to last element)
        """

        # if not loop_uv:
        loop_uv = {}

        looped = False
        first_loop = True
        prev_uv = uv_m

        while True:
            uv_adjacentLoop = {}
            for loop in loop_m.vert.link_loops:
                uv_data = loop[uv_layer]
                uv = tuple(uv_data.uv)
                if uv != uv_m:
                    continue

                loop_uv[loop] = uv

                for index, adjacent_loop in enumerate((loop.link_loop_next, loop.link_loop_prev)):
                    uv_data = adjacent_loop[uv_layer]
                    uv = tuple(uv_data.uv)
                    if uv == prev_uv:
                        continue
                    if adjacent_loop in loop_uv:
                        looped = True
                        continue
                    uv_data = uv_data if (index == 1) else loop[uv_layer]
                    if uv_data.select_edge:
                        uv_adjacentLoop[uv] = adjacent_loop
            
            len_ = len(uv_adjacentLoop)
            if (len_ == 2 and first_loop) or (len_ == 1):
                prev_uv = uv_m
                uv_m, loop_m = tuple(uv_adjacentLoop.items())[0]  # Only go one way
                first_loop = False
            else:
                # Make sure to always return in counterclockwise order
                # https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
                # https://www.geeksforgeeks.org/area-of-a-polygon-with-given-n-ordered-vertices/

                uvs = {uv: None for uv in loop_uv.values()}
                duplicated_uvs = [uv for uv in uvs for _ in range(2)]
                duplicated_uvs.append(duplicated_uvs.pop(0))
                area = 0

                for i in range(0, len(duplicated_uvs), 2):
                    x1, y1 = duplicated_uvs[i]
                    x2, y2 = duplicated_uvs[i + 1]
                    area += (x2 - x1) * (y2 + y1)

                if area > 0: # If clockwise, reverse
                    new_loop_uv = {}
                    for loop in reversed(loop_uv):
                        new_loop_uv[loop] = loop_uv[loop]
                    loop_uv = new_loop_uv

                return loop_uv, looped

    @classmethod
    def search_island_edge_loops(cls, uv_layer, pre_active_loops, loops_done, to_search_islands):
        """
        For every island in "to_search_islands", with an island's active loops as base,
        return every edge loop found while continuously stepping outwards.

        Parameters
            - pre_active_loops --- Since uv selection data will be modified,  \
                                   this will be used to revert to pre-function-call state.
        """

        islands = []
        to_modify = []

        for kwargs in to_search_islands:
            island = {}
            if kwargs['loop_m'] in loops_done:
                continue
            island['active_loops'] = kwargs.pop('active_loops')

            loops, uv_uvVectors = cls.connected_in_same_island(uv_layer, **kwargs, loops_done=loops_done, get_uv_uvVector=True)
            loops_done.update(loops)
            if "ignore_island" in uv_uvVectors:  # If there is an edge loop in island already in to_modify
                continue

            island['loops'] = loops
            islands.append(island)

        for island in islands:
            loops = island['loops']
            active_loops = island['active_loops']
            current_active = active_loops
            prev_faces = set()

            while True:
                loops_to_search_edge = set()
                for loop in current_active:
                    face = loop.face
                    if face in prev_faces:
                        continue

                    inactive_loops = set()
                    for loop in face.loops:
                        if not loop[uv_layer].select:
                            inactive_loops.add(loop)

                    for loop in inactive_loops:
                        uv = loop[uv_layer].uv
                        for v_loop in loop.vert.link_loops:
                            uv_data = v_loop[uv_layer]
                            if uv_data.uv == uv:
                                uv_data.select = True
                                loops_to_search_edge.add(v_loop)

                    prev_faces.add(face)

                if not loops_to_search_edge:
                    for loop in current_active:
                        loop[uv_layer].select = False
                    break

                for loop in loops_to_search_edge:
                    if loop.link_loop_next in loops_to_search_edge:
                        loop[uv_layer].select_edge = True

                for loop in current_active:
                    loop[uv_layer].select = False

                current_active = loops_to_search_edge

                loop = next(iter(loops_to_search_edge))
                loop_uv, looped = SearchUV.connected_in_same_active_edge_loop(uv_layer, loop, tuple(loop[uv_layer].uv))

                if looped:
                    to_modify.append((loop_uv, active_loops))

        for loop in pre_active_loops:
            loop[uv_layer].select = True

        return to_modify
