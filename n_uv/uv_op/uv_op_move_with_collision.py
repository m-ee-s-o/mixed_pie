import bpy
from bpy.types import Operator
from mathutils import Vector
import bmesh
from .uv_utils import Base_UVOpsPoll, SearchUV


class MXD_OT_UV_MoveWithCollision(Base_UVOpsPoll, Operator):
    bl_idname = "uv.move_with_collision"
    bl_label = "Move With Collision"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move island except for when it collides with another"

    class InactiveIsland:
        def __init__(self, uv_uvVectors):
            self.uv_uvVectors = uv_uvVectors

            x = sorted(uv_uvVectors, key=lambda uv: uv[0])
            y = sorted(uv_uvVectors, key=lambda uv: uv[1])
            self._min_x = self.uv_uvVectors[x[0]][0]
            self._max_x = self.uv_uvVectors[x[-1]][0]
            self._min_y = self.uv_uvVectors[y[0]][0]
            self._max_y = self.uv_uvVectors[y[-1]][0]
            self.margin = 2/256

        @property
        def min_x(self):
            return round(self._min_x.x - self.margin, 6)

        @property
        def max_x(self):
            return round(self._max_x.x + self.margin, 6)

        @property
        def min_y(self):
            return round(self._min_y.y - self.margin, 6)

        @property
        def max_y(self):
            return round(self._max_y.y + self.margin, 6)

    class ActiveIsland(InactiveIsland):
        # POINTS_BOUND_DEF = (
        #     ("min_x", "min_y"),  # Bottom Left
        #     ("max_x", "min_y"),  # Bottom Right
        #     ("max_x", "max_y"),  # Top Right
        #     ("min_x", "max_y"),  # Top Left
        # )

        def __init__(self, uv_uvVectors, obj_data, uvData_uvSelectState):
            super().__init__(uv_uvVectors)
            self.obj_data = obj_data
            self.uvData_uvSelectState = uvData_uvSelectState
            self.width = self.max_x - self.min_x
            self.height = self.max_y - self.min_y
            self.check = True

        def revert(self):
            for uv_data, uv_select_state in self.uvData_uvSelectState:
                uv_data.select = uv_select_state

            for uv, uvVectors in self.uv_uvVectors.items():
                for uvVector in uvVectors:
                    uvVector[:] = uv

            bmesh.update_edit_mesh(self.obj_data)

        def move(self, i, offset, is_positive, islands):
            def get_sort_key(island):
                if i == 0:
                    return island.min_x if is_positive else island.max_x
                else:
                    return island.min_y if is_positive else island.max_y

            # def check_collision(i):
            #     self.corners = [(getattr(self, x), getattr(self, y)) for x, y in self.POINTS_BOUND_DEF]

            #     for island in sorted(islands, key=get_sort_key, reverse=not is_positive):
            #         # Exclude out of way islands
            #         if i == 0 and island.min_y > self.max_y or island.max_y < self.min_y:
            #             continue
            #         # elif i == 1 and island.

            #         for corner in self.corners:

            #             if i == 0 and island.min_x < corner[i] < island.max_x:
            #                 if is_positive:
            #                     x_offset = island.min_x - self.max_x
            #                 else:
            #                     x_offset = island.max_x - self.min_x

            #                 self.offset(x=x_offset)
            #                 check_collision(i)

            #                 return True

            #     return False

            # if i == 0 and check_collision(i):
            #     return
            hit = False

            for island in sorted(islands, key=get_sort_key, reverse=not is_positive):
                if i == 0:
                    # Exclude out of way islands
                    if island.min_y >= self.max_y or island.max_y <= self.min_y:
                        continue

                    if is_positive:
                        # Exclude islands behide of self
                        if island.min_x < self.max_x:
                            continue
                        hit = True
                        dx = island.min_x - self.max_x
                        self.offset(x=min(dx, offset))
                    else:
                        # Exclude islands ahead of self
                        if island.max_x > self.min_x:
                            continue
                        hit = True
                        dx = island.max_x - self.min_x
                        self.offset(x=max(dx, offset))
                    break
                else:
                    if island.min_x >= self.max_x or island.max_x <= self.min_x:
                        continue

                    if is_positive:
                        if island.min_y < self.max_y:
                            continue
                        hit = True
                        dy = island.min_y - self.max_y
                        self.offset(y=min(dy, offset))
                    else:
                        if island.max_y > self.min_y:
                            continue
                        hit = True
                        dy = island.max_y - self.min_y
                        self.offset(y=max(dy, offset))
                    break

            if not hit:  # No island in the way
                if i == 0:
                    if is_positive:
                        self.offset(x=min(1 - self.max_x, offset))
                    else:
                        self.offset(x=max(0 - self.min_x, offset))                    
                else:
                    if is_positive:
                        self.offset(y=min(1 - self.max_y, offset))
                    else:
                        self.offset(y=max(0 - self.min_y, offset))

        def offset(self, x=0, y=0):
            for i, val in enumerate((x, y)):
                if not val:
                    continue
                for uv, uvVectors in self.uv_uvVectors.items():
                    for uvVector in uvVectors:
                        uvVector[i] += val

            bmesh.update_edit_mesh(self.obj_data)

    def invoke(self, context, event):
        self.get_bounds(context)
        self.initial_cursor = Vector(bpy.context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y))
        self.axis = (True, True)
        context.window.cursor_modal_set('SCROLL_XY')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def get_bounds(self, context):
        self.active_islands = []
        self.inactive_islands = []
        for obj in {context.object, *context.selected_objects}:
            data = obj.data
            bm = bmesh.from_edit_mesh(data)
            uv_layer = bm.loops.layers.uv.active
            loops_done = set()

            def get(active=True):

                for vert in bm.verts:
                    if not vert.select:
                        continue
                    for loop in vert.link_loops:
                        if loop in loops_done:
                            continue
                        uv_data = loop[uv_layer]
                        uv = tuple(uv_data.uv)

                        # Start with active vertices
                        if active and not uv_data.select:
                            continue

                        loops, uv_uvVectors = SearchUV.connected_in_same_island(uv_layer, loop, uv, get_uv_uvVector=True)
                        loops_done.update(loops)

                        if active:
                            uvData_uvSelectState = []
                            # All vertices in the same island as an active vertex will also become active
                            for loop in loops:
                                uvData_uvSelectState.append((loop[uv_layer], loop[uv_layer].select))
                                loop[uv_layer].select = True

                            self.active_islands.append(self.ActiveIsland(uv_uvVectors, data, uvData_uvSelectState))
                        else:
                            island = self.InactiveIsland(uv_uvVectors)
                            if island.max_x <= 0 or island.min_x >= 1 or island.max_y <= 0 or island.min_y >= 1:
                                continue

                            self.inactive_islands.append(island)

            get()
            get(False)

            bmesh.update_edit_mesh(data)
            bm.free()

    def modal(self, context, event):
        context.area.tag_redraw()

        match event.type:
            case 'MOUSEMOVE':
                current_cursor = Vector(context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y))
                dxy = current_cursor - self.initial_cursor
                for i, val in enumerate(self.axis):
                    if not val:
                        dxy[i] = 0
                
                for i in range(2):
                    if not dxy[i]:
                        continue

                    is_positive = (dxy[i] > 0)

                    def sort_key(island):
                        if i == 0:
                            return island.max_x if is_positive else island.min_x
                        else:
                            return island.max_y if is_positive else island.min_y

                    for island in sorted(self.active_islands, key=sort_key, reverse=is_positive):
                        island.move(i, dxy[i], is_positive, (*self.inactive_islands, *(i for i in self.active_islands if i != island)))
                
                region = context.region
                warp = [None, None]
                if event.mouse_region_x <= 0:
                    warp[0] = region.x + region.width
                elif event.mouse_region_x >= region.width - 1:  # -1, won't work otherwise
                    warp[0] = region.x
                
                if event.mouse_region_y <= 0:
                    warp[1] = region.y + region.height
                elif event.mouse_region_y >= region.height:
                    warp[1] = region.y

                if warp != [None, None]:
                    x, y = warp
                    x = x if x is not None else event.mouse_region_x
                    y = y if y is not None else event.mouse_region_y

                    context.window.cursor_warp(x, y)
                    current_cursor = Vector(context.region.view2d.region_to_view(x - region.x, y - region.y))

                self.initial_cursor = current_cursor

            case 'RIGHTMOUSE' | 'ESC' if event.value == 'PRESS':
                context.window.cursor_modal_restore()

                for island in self.active_islands:
                    island.revert()

                return {'CANCELLED'}
            
            case 'LEFTMOUSE':
                context.window.cursor_modal_restore()
                return {'FINISHED'}
            
            case 'X' if event.value == 'PRESS':
                self.toggle_axis('X')

            case 'Y' if event.value == 'PRESS':
                self.toggle_axis('Y')

        return {'RUNNING_MODAL'}

    def toggle_axis(self, axis):
        index = 0 if (axis == 'Y') else 1

        if self.axis[index]:
            self.axis = (False, True) if (axis == 'Y') else (True, False)
            bpy.context.window.cursor_modal_set(f'MOVE_{axis}')

            for island in self.active_islands:
                for uv, uvVectors in island.uv_uvVectors.items():
                    for uvVector in uvVectors:
                        uvVector[index] = uv[index]
                bmesh.update_edit_mesh(island.obj_data)

        else:
            self.axis = (True, True)
            bpy.context.window.cursor_modal_set('SCROLL_XY')


def register():
    bpy.utils.register_class(MXD_OT_UV_MoveWithCollision)


def unregister():
    bpy.utils.unregister_class(MXD_OT_UV_MoveWithCollision)
