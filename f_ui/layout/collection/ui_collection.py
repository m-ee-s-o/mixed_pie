from math import ceil
import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from ..ui_panel_layout import PanelLayout
from ..ui_box import Box
from ..ui_prop import CollectionProp
from ...utils.utils_box import make_box, point_inside
from ....a_utils.utils_func import recur_get_bone_collections, recur_get_bcoll_children


# TODO: Improve performance (obvious when moving main box).


class Collection:
    # msgbus = set()
    inherit = PanelLayout.inherit

    def __init__(self, parent, id, collection, draw_item_func):
        # TODO: When active_index changes (e.g., when adding new bone collection), scroll to focus on the new collection if its in last column and not within range

        # if id not in self.__class__.msgbus:
        #     def msgbus_callback():
        #         print(id)
        #     bpy.msgbus.subscribe_rna(
        #         key=bpy.context.object.path_resolve("data.collections.active_index", False),
        #         owner=id,
        #         args=(),
        #         notify=msgbus_callback,
        #     )
        #     bpy.msgbus.clear_by_owner(id)
        #     self.__class__.msgbus.add(id)

        type_ = type(collection.id_data)
        self.collection_identifier = collection.bl_rna.identifier
        properties_attr = f"MixedPie_UICollection_{self.collection_identifier}"
        if not hasattr(type_, properties_attr):
            from . import ui_collection_generated_props
            from .ui_collection_generated_props import register_template, unregister_template
            from pathlib import Path
            from importlib import reload

            file = Path(__file__).with_name("ui_collection_generated_props.py")
            with file.open("r+") as f:
                lines = f.readlines()

                register_index = None
                unregister_index = None

                for index, line in enumerate(lines):
                    if line.startswith("def register"):
                        register_index = index + 1
                    elif line.startswith("def unregister"):
                        unregister_index = index + 1
                
                lines.insert(unregister_index, unregister_template.replace("<id_data_identifier>", type_.__name__).replace("<properties_attr>", properties_attr))
                lines.insert(register_index, register_template.replace("<id_data_identifier>", type_.__name__).replace("<properties_attr>", properties_attr))

                f.truncate(0)
                f.seek(0)
                f.writelines(lines)

            module = reload(ui_collection_generated_props)
            from ....__init__ import modules
            for group in modules.values():
                if module.__name__ in group:
                    group[module.__name__] = module
            module.register()

        ui_collections_list = bpy.context.preferences.addons[__package__.partition(".")[0]].preferences.ui_collections.list
        if self.collection_identifier not in ui_collections_list:
            ui_collections_list.add().name = self.collection_identifier

        pref = ui_collections_list[self.collection_identifier]
        properties = getattr(collection.id_data, properties_attr)

        Box.__init__(self, parent, 500 * parent.ui_scale, 200 * parent.ui_scale, False, color=(0.5, 0.5, 0.5, 1))
        self.ITEM_HEIGHT = 40 * self.ui_scale
        # self.ITEM_HEIGHT = 44 * self.ui_scale
        self.SPACE_BETWEEN_ITEMS = 1
        self.SCROLL_BAR_WIDTH = 20 * self.ui_scale

        if not hasattr(self.root, "ui_collections"):
            self.root.ui_collections = set()
        if id in self.root.ui_collections:
            self.root.parent_modal_operator.clean()
            raise Exception(f'Repeating ID "{id}": Collection ID must be unique for each UI collection even if they display the same data.')
        self.root.ui_collections.add(id)
        self.id = id

        self.flow(horizontal=True)
        self.collection = collection
        self.draw_item_func = draw_item_func
        self.properties = properties

        self.MARGIN = int(self.MARGIN * 0.55)
        self.vMARGIN_TOP_LEFT = Vector((self.MARGIN, -self.MARGIN))

        if properties.settings_basis == 'GLOBAL':
            self.item_per_column_path = f"bpy.context.preferences.addons[__package__.partition('.')[0]].preferences.ui_collections.list['{self.collection_identifier}']"  \
                                        f".{'auto' if pref.column_definition_type == 'AUTOMATIC' else 'custom'}_item_per_column"
        else:
            self.item_per_column_path = f"{repr(properties.id_data)}.{properties.path_from_id(('auto' if properties.column_definition_type == 'AUTOMATIC' else 'custom')+'_item_per_column')}"

        self.height = self.ITEM_HEIGHT * eval(self.item_per_column_path)                  \
                      + self.SPACE_BETWEEN_ITEMS * (eval(self.item_per_column_path) - 1)  \
                      + self.MARGIN * 2

        self.collection_columns = self.children
        self.resize_columns = {}
        self.resize_ui_length = (self.ITEM_HEIGHT * 3)

        if self.collection.bl_rna.identifier == 'BoneCollections':
            colls =  recur_get_bone_collections(collection)  # Gets proper order better (tree recursive) vs armature.colections_all (Blender 4.1)
            search_src = collection.id_data.collections_all  # src should be bpy_prop_collection
        else:
            colls = collection
            search_src = collection

        if not colls:
            return
        
        def set_collection_columns(settings_basis):
            if settings_basis.column_definition_type == 'CUSTOM':
                uncategorized = {coll: None for coll in colls}
                if "Uncategorized" not in settings_basis.custom_columns:
                    settings_basis.custom_columns.add().name = "Uncategorized"

                all_items = set()
                all_columns = {}

                for col in settings_basis.custom_columns:
                    if col.name == "Uncategorized":
                        all_columns[settings_basis.custom_columns["Uncategorized"]] = None
                        continue

                    items = []

                    for i in col.items:
                        if (index := search_src.find(i.name)) != -1:
                            item = search_src[index]
                            if item in all_items:
                                continue
                            all_items.add(item)
                            if item.parent:
                                continue
                            items.append(item)
                            del uncategorized[item]
                            if item.children and item.is_expanded:
                                for child in recur_get_bcoll_children(item):
                                    items.append(child)
                                    del uncategorized[child]

                    all_columns[col] = items

                settings_basis.custom_columns["Uncategorized"].item_count = len(uncategorized)
                if uncategorized:
                    uncategorized = list(uncategorized)
                    all_columns[settings_basis.custom_columns["Uncategorized"]] = uncategorized

                for properties, items in all_columns.items():
                    if properties == settings_basis.custom_columns["Uncategorized"] and not items:
                        continue
                    CollectionColumn(self, items, properties)
            else:
                max_columns = max(1, ceil(len(colls) / settings_basis.auto_item_per_column))  # Should be at least 1
                max_column_amount = settings_basis.max_column_amount if settings_basis.max_column_amount <= max_columns else max_columns

                for i in range(max_column_amount):
                    if i == max_column_amount - 1:
                        items_amount = len(colls) - settings_basis.auto_item_per_column * i
                    else:
                        items_amount = min(len(colls), settings_basis.auto_item_per_column)

                    items = []
                    start_index = i * settings_basis.auto_item_per_column
                    for j in range(items_amount):
                        j += start_index
                        items.append(colls[j])

                    CollectionColumn(self, items, settings_basis.auto_columns[i])

        set_collection_columns(pref if properties.settings_basis == 'GLOBAL' else properties)

        self.width = sum(column.width for column in self.collection_columns) or (300 * self.ui_scale)

        self.resize_ui_inactive = []
        self.resize_color = (0.5, 0.5, 0.5, 1)

        Box.make(self)  # Make self.corners
        self.resizing = getattr(self.attr_holder, f"{self.id}_resizing_y", None)
        if not self.resizing:
            # Resize indicator UI
            bottom = self.corners.bottom_right.copy()
            bottom.x -= (self.width / 2) - (self.resize_ui_length / 2); self.resize_ui_inactive.append(bottom.copy())
            bottom.x -= self.resize_ui_length; self.resize_ui_inactive.append(bottom)

    def modal(self, context, event):
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS'  \
                and Box.point_inside(self, event) and (panel := getattr(self.parent_modal_operator, "collection_pref_panel", None)):
            panel.current_properties = self.properties
            panel.current_collection_identifier = self.collection_identifier
            bpy.ops.wm.call_panel(name=panel.__name__)
            event.handled = True
            return

        # if self.collection_columns:
        self.modal_resize_y(context, event)

    def modal_resize_y(self, context, event):
        signature = (self.id, "y")
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        if not self.resizing:
            # Bottom resize area
            _, corners = make_box(self.corners.bottom_left + Vector((0, self.MARGIN)), self.width, self.MARGIN * 2,
                                include_corners_copy=True, origin_point='TOP_LEFT')

            if point_inside(None, event, corners):
                self.attr_holder.hold = signature
                if context.object.type == 'ARMATURE':  # Cursor would jitter for modes like Weight Paint (it's automatically set for the mode every frame)
                    context.window.cursor_modal_set('MOVE_Y')
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    setattr(self.attr_holder, f"{self.id}_resizing_y", True)
                    self.resize_color = (0.8, 0.8, 0.8, 1)
                    self.attr_holder.initial_item_per_column = eval(self.item_per_column_path)
                event.handled = True

            elif self.attr_holder.hold == signature:
                context.window.cursor_modal_restore()
                self.attr_holder.hold = None
                event.handled = True

        if not self.resizing:
            return
        self.resize_color = (0.8, 0.8, 0.8, 1)
        parent, attr = self.item_per_column_path.rsplit(".", 1)

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                setattr(self.attr_holder, f"{self.id}_resizing_y", False)
                self.attr_holder.hold = None
                event.handled = True
            case 'ESC' if event.value == 'PRESS':
                setattr(eval(parent), attr, self.attr_holder.initial_item_per_column)
                setattr(self.attr_holder, f"{self.id}_resizing_y", False)
                event.handled = True
            case 'MOUSEMOVE':
                increment = self.ITEM_HEIGHT + self.SPACE_BETWEEN_ITEMS
                basis = self.origin.y - self.MARGIN
                dy = event.cursor.y - basis
                if dy < 0:  # Cursor is below self.origin.y. Would still resize even if the cursor is far above.
                    setattr(eval(parent), attr, int(abs(dy / increment)))
                event.handled = True

    def make(self):
        Box.make(self)

    def draw(self):
        Box.draw(self)
        for col in self.collection_columns:
            col.draw()

        gpu.state.line_width_set(2)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", self.resize_color)
        vertices = self.resize_ui_inactive
        if self.attr_holder.hold == (self.id, "y"):
            vertices = (self.corners.bottom_left, self.corners.bottom_right)
        line = batch_for_shader(shader, 'LINES', {'pos': vertices})
        line.draw(shader)
        gpu.state.line_width_set(1)

class CollectionColumn:
    inherit = PanelLayout.inherit
    auto_adjust_children = True

    def __init__(self, parent, items, properties=None):
        column_index = len(parent.collection_columns)
        if not properties:
            properties = parent.properties.columns[column_index]
        self.properties = properties

        if column_index == 0:
            self.no_spacing = True
        else:
            self.custom_spacing = 0

        Box.__init__(self, parent, 0, parent.height, color=(0.05, 0.05, 0.05, 1))

        properties.column_index = column_index
        properties.item_count = len(items)
        properties.item_per_column = eval(parent.item_per_column_path)
        self.width = properties.width * self.ui_scale

        self.make_collection_items(parent, items)
        self.make_scroll_bar()
        self.make_resize_ui()

    def make_collection_items(self, parent, items):
        self.collection_items = []

        for i in range(min(self.properties.item_per_column, len(items))):
            i += self.properties.start_index
            item = CollectionItem(self, self.width - (self.MARGIN * 2), parent.ITEM_HEIGHT,
                                  draw_func=parent.draw_item_func, collection=parent.collection, item=items[i])
            self.collection_items.append(item)

    def make_resize_ui(self):
        self.resize_ui_inactive = []
        self.resize_color = (0.5, 0.5, 0.5, 1)

        Box.make(self)  # Make self.corners

        if not hasattr(self.attr_holder, "collection_resize_column_id_indices"):
            self.attr_holder.collection_resize_column_id_indices = {}

        resize = (self.properties.column_index in self.attr_holder.collection_resize_column_id_indices)
        if not resize:
            # Resize indicator UI
            right = self.corners.top_right.copy()
            right.y -= (self.height / 2) - (self.parent.resize_ui_length / 2); self.resize_ui_inactive.append(right.copy())
            right.y -= self.parent.resize_ui_length; self.resize_ui_inactive.append(right)

    def make_scroll_bar(self):
        if self.properties.item_per_column >= self.properties.item_count or not self.children:  # If there are no items left to scroll
            return

        self.flow(horizontal=True)
        self.current_element = self.children[0]
        self.scroll_bar = CollectionScrollBar(self)
        self.width += self.parent.SCROLL_BAR_WIDTH + self.MARGIN

    def modal(self, context, event):
        if hasattr(self, "scroll_bar"):
            self.modal_scoll(context, event)
        self.modal_resize_x(context, event)

    def modal_scoll(self, context, event):
        signature = (self.parent.id, f"scroll {self.properties.column_index}")
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        match event.type:
            case 'WHEELUPMOUSE' if Box.point_inside(self, event):
                self.properties.start_index -= 1
                self.root.draw_again = True
                event.handled = True
                return
            case 'WHEELDOWNMOUSE' if Box.point_inside(self, event):
                self.properties.start_index += 1
                self.root.draw_again = True
                event.handled = True
                return

        cursor = event.cursor
        basis = getattr(self.attr_holder, f"{self.parent.id}_scroll_basis", False)

        if not basis:
            if self.scroll_bar.scroll.point_inside(cursor):
                self.attr_holder.hold = signature
                self.scroll_bar.scroll.color = (0.5, 0.5, 0.5, 1)
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    setattr(self.attr_holder, f"{self.parent.id}_scroll_basis", cursor.y)
                    self.attr_holder.collection_scroll_prior_start_index = self.properties.start_index
            elif self.attr_holder.hold == signature:
                self.attr_holder.hold = None

        if not basis:
            return
        self.scroll_bar.scroll.color = (0.5, 0.5, 0.5, 1)

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                    delattr(self.attr_holder, f"{self.parent.id}_scroll_basis")
                    # setattr(self.attr_holder, f"{self.parent.id}_scroll_basis", None)
            case 'MOUSEMOVE':
                if (basis := getattr(self.attr_holder, f"{self.parent.id}_scroll_basis", False)):
                    steps = (cursor.y - basis) / self.scroll_bar.scroll_increment
                    self.properties.start_index = self.attr_holder.collection_scroll_prior_start_index - int(steps)

    def modal_resize_x(self, context, event):
        signature = (self.parent.id, self.properties.column_index)
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        cursor = event.cursor
        x_resize_click = getattr(self.attr_holder, f"{self.parent.id}_x_resize_click", None)

        if not x_resize_click:
            # Right resize UI
            _, corners = make_box(self.corners.top_right - Vector((self.MARGIN, 0)), self.MARGIN * 2, self.height,
                                    include_corners_copy=True, origin_point='TOP_LEFT')

            if point_inside(None, event, corners):
                self.attr_holder.hold = signature
                if context.object.type == 'ARMATURE':  # Cursor would jitter for modes like Weight Paint (it's set for the mode)
                    context.window.cursor_modal_set('MOVE_X')
                self.attr_holder.collection_resize_column_id_indices = {
                    (self.parent.id, column.properties.column_index) for column in ((self, ) if event.ctrl else {*self.parent.collection_columns})
                }
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.resize_color = (0.8, 0.8, 0.8, 1)
                    setattr(self.attr_holder, f"{self.parent.id}_x_resize_click", cursor.x)
                    self.attr_holder.collection_resize_column_initial_prop_widths = {
                        index: self.parent.collection_columns[index].properties.width for _, index in self.attr_holder.collection_resize_column_id_indices
                    }
            elif self.attr_holder.hold == signature:
                self.attr_holder.collection_resize_column_id_indices = {}
                context.window.cursor_modal_restore()
                self.attr_holder.hold = None

        if not x_resize_click:
            return
        self.resize_color = (0.8, 0.8, 0.8, 1)

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                setattr(self.attr_holder, f"{self.parent.id}_x_resize_click", None)
                self.attr_holder.collection_resize_column_initial_prop_widths = None
            case 'ESC' if event.value == 'PRESS':
                for index, width in self.attr_holder.collection_resize_column_initial_prop_widths.items():
                    column = self.parent.collection_columns[index]
                    column.properties.width = width
                setattr(self.attr_holder, f"{self.parent.id}_x_resize_click", None)
                self.attr_holder.collection_resize_column_initial_prop_widths = None
                event.handled = True
            case 'MOUSEMOVE':
                cursor_dx = cursor.x - x_resize_click
                initial_prop_widths = self.attr_holder.collection_resize_column_initial_prop_widths
                prior = self.properties.width
                self.properties.width = initial_prop_widths[self.properties.column_index] + int(cursor_dx / self.ui_scale)
                # /ui_scale since cursor distance should be already scaled and properties.width shouldn't be scaled

                self.width = self.properties.width * self.ui_scale  # Immediately take effect in the next draw (after this modal)
                if hasattr(self, "scroll_bar"):
                    self.width += self.parent.SCROLL_BAR_WIDTH + self.MARGIN
                if prior == self.properties.width:
                    return

                diff_prop_width = self.properties.width - initial_prop_widths[self.properties.column_index]
                total_width = self.width

                id_indices = set(self.attr_holder.collection_resize_column_id_indices)
                id_indices.remove((self.parent.id, self.properties.column_index))
                for _, index in id_indices:
                    column = self.parent.collection_columns[index]
                    column.properties.width = initial_prop_widths[column.properties.column_index] + diff_prop_width
                    column.width = column.properties.width * self.ui_scale
                    if hasattr(column, "scroll_bar"):
                        column.width += self.parent.SCROLL_BAR_WIDTH + self.MARGIN
                    total_width += column.width
                diff_total_width = total_width - self.parent.width
                self.parent.width = total_width

                self.resize_clean_up()

                children = set(self.root.recur_get_all_children(self.parent))
                for element in self.root.elements:
                    if element not in children:
                        if self.origin.y > element.origin.y > self.origin.y - self.height           \
                                or self.origin.y > element.origin.y - element.height > self.origin.y - self.height:  # If element's head or toe is inside
                            element.origin.x += diff_total_width

    def resize_clean_up(self):
        columns = self.parent.collection_columns
        for i, column in enumerate(columns):
            child_width = column.width - (column.MARGIN * 2)
            if (scroll_bar := getattr(column, "scroll_bar", None)):
                # If there is a scroll bar, a column's width at this point already has space for the bar...
                child_width -= self.parent.SCROLL_BAR_WIDTH + column.MARGIN  # ...so decrease it.
                scroll_bar.case.origin.x = column.origin.x + child_width + (column.MARGIN * 2)
                scroll_bar.scroll.origin.x = scroll_bar.case.origin.x
            for child in column.collection_items:
                if isinstance(child, CollectionItem):
                    child.width = child_width
            if i != 0:
                previous = columns[i - 1]
                new_origin_x = previous.origin.x + previous.width
                self.root.recur_offset_children_origin(column, offset_x=new_origin_x - column.origin.x)
                column.origin.x = new_origin_x

    def make(self):
        Box.make(self)

    def draw(self):
        # Box.make(self)
        # Box.draw(self)

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", self.resize_color)
        resize = ((self.parent.id, self.properties.column_index) in self.attr_holder.collection_resize_column_id_indices)
        if resize:
            gpu.state.line_width_set(2)
            
        if (len(self.parent.collection_columns) > 1
                and self is not self.parent.collection_columns[-1]  # Not last, since right border line has rounded corners
                or resize):  # Division line
            batch_for_shader(shader, 'LINES', {'pos': (self.corners.top_right, self.corners.bottom_right)}).draw(shader)

        if not resize:
            gpu.state.line_width_set(2)
            batch_for_shader(shader, 'LINES', {'pos': self.resize_ui_inactive}).draw(shader)
        gpu.state.line_width_set(1)


class CollectionScrollBar:
    def __init__(self, column):
        width = column.parent.SCROLL_BAR_WIDTH
        self.case = Box(column, width, column.height - (column.MARGIN * 2), False, color=(0.333, 0.333, 0.333, 1))
        self.scroll = Box(column, width, 0, color=(0.333, 0.333, 0.333, 1))

        self.scroll_increment = self.case.height / column.properties.item_count
        self.scroll.height = self.scroll_increment * column.properties.item_per_column
        self.scroll.origin = self.case.origin.copy()
        self.scroll.origin.y -= self.scroll_increment * column.properties.start_index
        self.scroll.make()


class CollectionItem:
    inherit = PanelLayout.inherit
    auto_adjust_children = True
    adjustable = True

    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop("collection")
        self.draw_func = kwargs.pop("draw_func")
        self.item = kwargs.pop("item")
        self.active = (self.collection.active == self.item)
        parent = args[0]
        self.custom_spacing = parent.parent.SPACE_BETWEEN_ITEMS
        Box.__init__(self, *args, **kwargs)
        self.flow(horizontal=True)

        def recur_how_many_parents(child, cnt=0):
            if child.parent != None:
                cnt = recur_how_many_parents(child.parent, cnt=cnt + 1)
            return cnt

        for _ in range(recur_how_many_parents(self.item)):
            self.label("  ").adjustable = False

        pre = self.root.icon_scale
        self.root.icon_scale = 0.5

        def offset(prop):
            dx = self.origin.x - prop.origin.x
            prop.origin.x += dx
            if hasattr(prop, "icon_box"):
                prop.icon_box.origin.x += dx
            if hasattr(prop, "label_box"):
                prop.label_box.origin.x += dx

        if self.item.children:
            prop = self.prop(self.item, "is_expanded", icon='DOWNARROW_HLT' if self.item.is_expanded else 'RIGHTARROW', emboss=False)
            offset(prop)
        else:
            prop = self.prop(self.item, "is_expanded", icon='BLANK1', emboss=False)
            prop.dud = True
            offset(prop)

        self.root.icon_scale = pre

        # Make here since there are modal dependent elements and modals are read reversed
        self.draw_func(self, self.collection, self.item)
        PanelLayout.adjust(self)

    def label(self, text):
        label = PanelLayout.label(self, text)
        label.center_y = True
        return label

    def text(self, data, property):
        txt = PanelLayout.text(self, data, property)
        txt.center_y = True
        return txt

    def operator(self, id_name, label="", icon=None, emboss=True):
        op = PanelLayout.operator(self, id_name, label, icon, emboss)
        op.center_y = True
        return op

    def prop(self, data, property, label="", icon=None, emboss=True):
        prop = PanelLayout.prop(self, data, property, label, icon, emboss)
        prop.center_y = True
        return prop

    def collection_prop(self, collection, item, property_path, label="", icon=None, emboss=True):
        prop = CollectionProp(self, collection, item, property_path, label, icon, emboss)
        prop.center_y = True
        return prop

    def modal(self, context, event):
        if self.attr_holder.hold:
            return
        Box.make(self)
        if Box.point_inside(self, event):
            self.inside = True
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.collection.active = self.item
                
                match self.collection.rna_type.identifier:
                    case "BoneCollections":
                        for area in context.screen.areas:
                            if area.type == 'PROPERTIES' and area.spaces[0].context == 'DATA':
                                for region in area.regions:
                                    if region.type == 'WINDOW':
                                        region.tag_redraw()
                                        break
        else:
            self.inside = False

    def make(self):
        # TODO: Make notifiers so that there would be no needless adjusting if not resized
        PanelLayout.adjust(self)  # Column may have been resized, readjust
        Box.make(self)
        inside = getattr(self, "inside", None)
        active = self.active
        if inside and not active:
            self.color = (0.139, 0.139, 0.139, 1)
        else:
            self.color = (0.278, 0.447, 0.702, 1)

    def draw(self):
        if self.active or (getattr(self, "inside", None)):
            Box.draw(self)


# TODO: Automatically focus the active item if out of view
            # Wrap add, remove, moveup, movedown collection, and set a cls variable in collection class.

# @bpy.app.handlers.persistent
# def notifier(_):
#     subscribe_to = bpy.context.object.data.path_resolve("collections.active_index", False)

#     def msgbus_callback(*args):
#         # This will print:
#         # Something changed! (1, 2, 3)
#         print("Something changed!", args)

#     bpy.msgbus.subscribe_rna(
#         key=subscribe_to,
#         owner="owner",
#         args=(1, 2, 3),
#         notify=msgbus_callback,
#     )

# def register():
#     bpy.app.handlers.load_post.append(notifier)

# def unregister():
#     bpy.app.handlers.load_post.remove(notifier)
