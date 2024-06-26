from math import ceil
import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from ..ui_panel_layout import PanelLayout
from ..ui_box import Box, Bounds
from ..ui_label import LabelBox
from ..ui_prop import CollectionProp
from ...utils.utils_box import point_inside
from ....a_utils.utils_func import recur_get_bone_collections, recur_get_bcoll_children


# TODO: Improve performance (obvious when moving main box).


class Collection(Bounds):
    # msgbus = set()
    inherit = PanelLayout.inherit
    custom_spacing_between_children = 0

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
        self.initial_child_origin = self.origin.copy()  # By default it's origin - vMARGIN_TOP_LEFT

        if properties.settings_basis == 'GLOBAL':
            self.item_per_column_path = f"bpy.context.preferences.addons[__package__.partition('.')[0]].preferences.ui_collections.list['{self.collection_identifier}']"  \
                                        f".{'auto' if pref.column_definition_type == 'AUTOMATIC' else 'custom'}_item_per_column"
        else:
            self.item_per_column_path = f"{repr(properties.id_data)}.{properties.path_from_id(('auto' if properties.column_definition_type == 'AUTOMATIC' else 'custom')+'_item_per_column')}"

        settings_basis = pref if properties.settings_basis == 'GLOBAL' else properties
        self.settings_basis = settings_basis

        self.collection_columns = self.children
        self.resize_columns = {}
        self.resize_ui_length = (self.ITEM_HEIGHT * 3)

        if self.collection.bl_rna.identifier == 'BoneCollections':
            colls =  recur_get_bone_collections(collection)  # Gets proper order better (tree recursive) vs armature.colections_all (Blender 4.1)
            search_src = collection.id_data.collections_all  # src should be bpy_prop_collection
        else:
            colls = collection
            search_src = collection

        if settings_basis.column_definition_type == 'CUSTOM':
            if "Uncategorized" not in settings_basis.custom_columns:
                settings_basis.custom_columns.add().name = "Uncategorized"
            settings_basis.custom_columns["Uncategorized"].item_count = 0

        if colls:
            # region: Set Collection Columns
            if settings_basis.column_definition_type == 'CUSTOM':
                uncategorized = {coll: None for coll in colls}

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
                self.all_items_count = len(colls)
                max_columns = max(1, ceil(self.all_items_count / settings_basis.auto_item_per_column))  # Should be at least 1
                max_column_amount = settings_basis.max_column_amount if settings_basis.max_column_amount <= max_columns else max_columns

                for i in range(max_column_amount):
                    if i == max_column_amount - 1:
                        items_amount = self.all_items_count - settings_basis.auto_item_per_column * i
                    else:
                        items_amount = min(self.all_items_count, settings_basis.auto_item_per_column)

                    items = []
                    start_index = i * settings_basis.auto_item_per_column
                    for j in range(items_amount):
                        j += start_index
                        items.append(colls[j])

                    CollectionColumn(self, items, settings_basis.auto_columns[i])
            # endregion

            self.longest_column = max(self.collection_columns, key=lambda column: len(column.collection_items))
            bottommost = self.longest_column.collection_items[-1]
            self.height = max(self.origin.y - bottommost.origin.y + bottommost.height + self.longest_column.MARGIN, self.height)

            for col in self.collection_columns:
                col.height = self.height

        self.width = sum(column.width for column in self.collection_columns) or (300 * self.ui_scale)  # or some_default_width

        # The following are still needed even if there are no columns
        self.resize_ui_inactive = []
        self.resize_color = (0.5, 0.5, 0.5, 1)

        self.resizing = getattr(self.attr_holder, f"{self.id}_resizing_y", None)
        if not self.resizing:
            # Resize indicator UI
            bottom = self.bottom_right
            bottom.x -= (self.width / 2) - (self.resize_ui_length / 2); self.resize_ui_inactive.append(bottom.copy())
            bottom.x -= self.resize_ui_length; self.resize_ui_inactive.append(bottom)
        
        if not hasattr(self.attr_holder, "collection_resize_column_id_indices"):
            self.attr_holder.collection_resize_column_id_indices = set()

    def modal(self, context, event):
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS'  \
                and Box.point_inside(self, event) and (panel := getattr(self.parent_modal_operator, "collection_pref_panel", None)):
            panel.current_properties = self.properties
            panel.current_collection_identifier = self.collection_identifier
            bpy.ops.wm.call_panel(name=panel.__name__)
            event.handled = True
            return

        if self.collection_columns:
            self.modal_resize_y(context, event)

    def modal_resize_y(self, context, event):
        signature = (self.id, "y")
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        if not self.resizing:
            # Bottom resize area
            if point_inside(None, event, (Vector((self.left, self.bottom + self.MARGIN)), self.width, self.MARGIN * 2)):
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
                event.handled = True

            case 'ESC' if event.value == 'PRESS':
                setattr(eval(parent), attr, self.attr_holder.initial_item_per_column)
                setattr(self.attr_holder, f"{self.id}_resizing_y", False)
                event.handled = True

            case 'MOUSEMOVE':
                event.handled = True
                basis = self.origin.y - self.height

                dy = basis - event.cursor.y
                increment = self.ITEM_HEIGHT + self.SPACE_BETWEEN_ITEMS

                if abs(dy) < increment:
                    return
                
                new_item_per_column = eval(self.item_per_column_path) + int(dy / increment)
                current_max_item_count = max(col.properties.item_count for col in self.collection_columns)

                if dy < 0:  # Resizing to upwards (decreasing)
                    if eval(self.item_per_column_path) > current_max_item_count:  # By setting it in the properties panel (right-click)
                        # Cut it short to suite current resizing
                        setattr(eval(parent), attr, current_max_item_count)
                
                max_item_count = self.all_items_count if self.settings_basis.column_definition_type == 'AUTOMATIC' else current_max_item_count

                if new_item_per_column > max_item_count:
                    # This will prevent oversizing the column if there's no more items. However, oversizing can still be done in the properties panel if wanted.
                    setattr(eval(parent), attr, max_item_count)  # Snap property to max_item_count
                    return

                setattr(eval(parent), attr, new_item_per_column)

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
            vertices = (self.bottom_left, self.bottom_right)
        line = batch_for_shader(shader, 'LINES', {'pos': vertices})
        line.draw(shader)
        gpu.state.line_width_set(1)

class CollectionColumn(Bounds):
    inherit = PanelLayout.inherit
    custom_spacing_between_children = 0

    def __init__(self, parent, items, properties=None):
        column_index = len(parent.collection_columns)
        if not properties:
            properties = parent.properties.columns[column_index]
        self.properties = properties

        Box.__init__(self, parent, 0, parent.height, color=(0.05, 0.05, 0.05, 1))

        properties.column_index = column_index
        properties.item_count = len(items)
        properties.item_per_column = eval(parent.item_per_column_path)
        self.width = properties.width * self.ui_scale

        if parent.settings_basis.column_definition_type == 'CUSTOM':
            with self.root.ChangeTemporarily(self.root.text_alignment, "active", 'CENTER'):
                category_label = PanelLayout.label(self, properties.name)
                category_label.text_size *= 1.05
                category_label.label_color = (0.757, 0.855, 1, 1)
                category_label.width = self.width - (self.MARGIN * 2)
                category_label.height = parent.ITEM_HEIGHT

            # Make some space between label and first item
            self.current_element = self
            self.initial_child_origin = category_label.origin.copy()
            self.initial_child_origin.y -= category_label.height + self.MARGIN

        self.make_collection_items(parent, items)
        self.make_scroll_bar()
        self.resize_ui_inactive = []
        self.resize_color = (0.5, 0.5, 0.5, 1)

    def make_collection_items(self, parent, items):
        self.collection_items = []
        max = min(self.properties.item_per_column, len(items))

        for i in range(max):
            i += self.properties.start_index
            item = CollectionItem(self, self.width - (self.MARGIN * 2), parent.ITEM_HEIGHT,
                                  draw_func=parent.draw_item_func, collection=parent.collection, item=items[i])
            if i != max - 1:
                item.origin.y -= parent.SPACE_BETWEEN_ITEMS
            self.collection_items.append(item)

    def make_scroll_bar(self):
        if self.properties.item_per_column >= self.properties.item_count or not self.collection_items:  # If there are no items left to scroll
            return

        self.flow(horizontal=True)
        self.current_element = self.collection_items[0]
        self.custom_spacing_between_children = None
        self.scroll_bar = CollectionScrollBar(self)
        self.custom_spacing_between_children = 0
        increment = self.parent.SCROLL_BAR_WIDTH + (self.MARGIN * 1.25)
        self.width += increment

        category_name = self.children[0]
        if isinstance(category_name, LabelBox):
            category_name.width += increment

    def modal(self, context, event):
        if hasattr(self, "scroll_bar"):
            self.modal_scoll(context, event)
        self.modal_resize_x(context, event)

    def modal_scoll(self, context, event):
        signature = (self.parent.id, f"scroll {self.properties.column_index}")
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        if Box.point_inside(self, event):
            match event.type:
                case 'WHEELUPMOUSE':
                    self.properties.start_index -= 1
                    self.root.reinitialize = True
                    event.handled = True
                    return
                case 'WHEELDOWNMOUSE':
                    self.properties.start_index += 1
                    self.root.reinitialize = True
                    event.handled = True
                    return

        cursor = event.cursor
        basis = getattr(self.attr_holder, f"{(self.parent.id, self.properties.column_index)}_scroll_basis", False)

        if not basis:
            if self.scroll_bar.scroll.point_inside(cursor):
                self.attr_holder.hold = signature
                self.scroll_bar.scroll.color = (0.5, 0.5, 0.5, 1)
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    setattr(self.attr_holder, f"{(self.parent.id, self.properties.column_index)}_scroll_basis", cursor.y)
                    self.attr_holder.collection_scroll_prior_start_index = self.properties.start_index
            elif self.attr_holder.hold == signature:
                self.attr_holder.hold = None

        if not basis:
            return
        self.scroll_bar.scroll.color = (0.5, 0.5, 0.5, 1)

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                    delattr(self.attr_holder, f"{(self.parent.id, self.properties.column_index)}_scroll_basis")
            case 'MOUSEMOVE':
                if (basis := getattr(self.attr_holder, f"{(self.parent.id, self.properties.column_index)}_scroll_basis", False)):
                    steps = (cursor.y - basis) / self.scroll_bar.scroll_increment
                    self.properties.start_index = self.attr_holder.collection_scroll_prior_start_index - int(steps)

    def modal_resize_x(self, context, event):
        signature = (self.parent.id, self.properties.column_index)
        if self.attr_holder.hold and self.attr_holder.hold != signature:
            return

        cursor = event.cursor
        x_resize_click = getattr(self.attr_holder, f"{signature}_x_resize_click", None)

        if not x_resize_click:
            # Right resize UI
            if point_inside(None, event, ((self.right - self.MARGIN, self.top), self.MARGIN * 2, self.height)):
                self.attr_holder.hold = signature
                if context.object.type == 'ARMATURE':  # Cursor would jitter for modes like Weight Paint (it's set for the mode)
                    context.window.cursor_modal_set('MOVE_X')
                self.attr_holder.collection_resize_column_id_indices = {
                    (self.parent.id, column.properties.column_index) for column in ((self, ) if event.ctrl else self.parent.collection_columns)
                }
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.resize_color = (0.8, 0.8, 0.8, 1)
                    setattr(self.attr_holder, f"{signature}_x_resize_click", cursor.x)
                    self.attr_holder.collection_resize_column_initial_prop_widths = {
                        index: self.parent.collection_columns[index].properties.width for _, index in self.attr_holder.collection_resize_column_id_indices
                    }
            elif self.attr_holder.hold == signature:
                self.attr_holder.collection_resize_column_id_indices = set()
                context.window.cursor_modal_restore()
                self.attr_holder.hold = None

        if not x_resize_click:
            return

        match event.type:
            case 'LEFTMOUSE' if event.value == 'RELEASE':
                setattr(self.attr_holder, f"{signature}_x_resize_click", None)
                self.attr_holder.collection_resize_column_initial_prop_widths = None
            case 'ESC' if event.value == 'PRESS':
                for index, width in self.attr_holder.collection_resize_column_initial_prop_widths.items():
                    column = self.parent.collection_columns[index]
                    column.properties.width = width
                setattr(self.attr_holder, f"{signature}_x_resize_click", None)
                self.attr_holder.collection_resize_column_initial_prop_widths = None
                event.handled = True
            case 'MOUSEMOVE':
                cursor_dx = cursor.x - x_resize_click
                initial_prop_widths = self.attr_holder.collection_resize_column_initial_prop_widths
                self.properties.width = initial_prop_widths[self.properties.column_index] + int(cursor_dx / self.ui_scale)
                # /ui_scale since cursor distance should be already scaled and properties.width shouldn't be scaled

                diff_prop_width = self.properties.width - initial_prop_widths[self.properties.column_index]

                id_indices = set(self.attr_holder.collection_resize_column_id_indices)
                id_indices.remove(signature)
                for _, index in id_indices:
                    column = self.parent.collection_columns[index]
                    column.properties.width = initial_prop_widths[column.properties.column_index] + diff_prop_width
                    column.width = column.properties.width * self.ui_scale
                    if hasattr(column, "scroll_bar"):
                        column.width += self.parent.SCROLL_BAR_WIDTH + self.MARGIN

                self.root.reinitialize = True
                event.handled = True

    def make(self):
        Box.make(self)

        if (self.parent.id, self.properties.column_index) not in self.attr_holder.collection_resize_column_id_indices:
            # Resize indicator UI
            top_right = self.top_right
            top_right.y -= (self.height / 2) - (self.parent.resize_ui_length / 2); self.resize_ui_inactive.append(top_right.copy())
            top_right.y -= self.parent.resize_ui_length; self.resize_ui_inactive.append(top_right)

    def draw(self):
        # Box.make(self)
        # self.color = (1, 1, 1, 1)
        # Box.draw(self)

        if getattr(self.attr_holder, f"{(self.parent.id, self.properties.column_index)}_x_resize_click", None):
            self.resize_color = (0.8, 0.8, 0.8, 1)

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", self.resize_color)
        resizing = (self.parent.id, self.properties.column_index) in self.attr_holder.collection_resize_column_id_indices

        if resizing:
            gpu.state.line_width_set(2)

        if (len(self.parent.collection_columns) > 1
                and self is not self.parent.collection_columns[-1]  # Not last, since right border line has rounded corners
                or resizing):  # Division line
            batch_for_shader(shader, 'LINES', {'pos': (self.top_right, self.bottom_right)}).draw(shader)

        if not resizing:
            gpu.state.line_width_set(2)
            batch_for_shader(shader, 'LINES', {'pos': self.resize_ui_inactive}).draw(shader)
        gpu.state.line_width_set(1)


class CollectionScrollBar:
    def __init__(self, column):
        first = column.collection_items[0]
        last = column.collection_items[-1]
        height = first.origin.y - last.origin.y + last.height
        width = column.parent.SCROLL_BAR_WIDTH

        self.case = Box(column, width, height, False, color=(0.333, 0.333, 0.333, 1))
        self.scroll = Box(column, width, 0, color=(0.333, 0.333, 0.333, 1))

        self.scroll_increment = self.case.height / column.properties.item_count
        self.scroll.height = self.scroll_increment * column.properties.item_per_column
        self.scroll.origin = self.case.origin.copy()
        self.scroll.origin.y -= self.scroll_increment * column.properties.start_index
        self.scroll.make()


class CollectionItem(Bounds):
    inherit = PanelLayout.inherit
    adjustable = True

    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop("collection")
        self.draw_func = kwargs.pop("draw_func")
        self.item = kwargs.pop("item")
        self.active = (self.collection.active == self.item)
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
