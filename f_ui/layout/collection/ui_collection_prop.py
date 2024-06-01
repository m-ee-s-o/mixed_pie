from math import ceil
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty
from ....a_utils.utils_prop import MXD_CollT_Name


class MXD_Obj_CollT_UI_Collection_Column(PropertyGroup):
    def get_start_index(self):
        if self.get("_start_index"):
            # Validate since start_index can make IndexError (in CollectionColumnn.make_cllection_items) when item_count changes
            if self['_start_index'] > (max := self.item_count - self.item_per_column):
                self['_start_index'] = max
            return self['_start_index']
        else:
            return 0

    def set_start_index(self, value):
        if value < 0:
              # Set to a value instead of just using "return" since value can go from 3 directly to -3 (some sort of frame drop if scroll is scrubbed very fast)
            self['_start_index'] = 0
        elif value > self.item_count - self.item_per_column:
            self['_start_index'] = self.item_count - self.item_per_column
        else:
            self['_start_index'] = value

    def set_width(self, value):
        self['_width'] = value if (value >= self.minimum_width) else self.minimum_width

    name: StringProperty(name="", default="Column")
    width: IntProperty(name="", get=lambda self: self.get("_width", 300), set=set_width)
    minimum_width = 150
    item_per_column: IntProperty()
    item_count: IntProperty()
    column_index: IntProperty()
    start_index: IntProperty(get=get_start_index, set=set_start_index)
    items: CollectionProperty(type=MXD_CollT_Name)
    active_item_index: IntProperty()


COLUMN_DEFINITION_TYPE = (('AUTOMATIC', "Automatic", "Automatically put items in columns according to settings"),
                          ('CUSTOM', "Custom", "Define a column, column name and names of its items. Items that doens't belong to a column will be put into an \"Uncategorized\" column"))


class MXD_Pref_UI_Collection(PropertyGroup):
    def get_max_column_amount(self):
        amount = self.get("_max_column_amount", 2)

        difference = amount - len(self.auto_columns)
        if difference > 0:
            for _ in range(difference):
                self.auto_columns.add()
        elif difference < 0:
            for _ in range(abs(difference)):
                del self.auto_columns[-1]

        return amount

    def set_max_column_amount(self, value):
        if value == self.max_column_amount:
            return
        if value < 1:
            return
        else:
            self['_max_column_amount'] = value

    @staticmethod
    def get_item_per_column(self, attr):
        return self.get(attr, self.default_item_per_column)

    @staticmethod
    def set_item_per_column(self, attr, value):
        if value < self.minimum_item_per_column:
            self[attr] = self.minimum_item_per_column
            return
        
        # # Don't allow to extend if there's no more items unseen
        # collection_len = self.total_item_count
        # current = self[attr]
        # if collection_len and value > current and value > collection_len:
        #     self[attr] = collection_len
        #     return

        self[attr] = value

    def get_auto_item_per_column(self):
        return MXD_Pref_UI_Collection.get_item_per_column(self, 'auto_item_per_column')

    def set_auto_item_per_column(self, value):
        MXD_Pref_UI_Collection.set_item_per_column(self, 'auto_item_per_column', value)

    def get_custom_item_per_column(self):
        return MXD_Pref_UI_Collection.get_item_per_column(self, 'custom_item_per_column')

    def set_custom_item_per_column(self, value):
        MXD_Pref_UI_Collection.set_item_per_column(self, 'custom_item_per_column', value)

    # Automatic
    minimum_item_per_column: IntProperty(default=5)
    default_item_per_column: IntProperty(default=9)
    max_column_amount: IntProperty(name="Column Amount", get=get_max_column_amount, set=set_max_column_amount)
    auto_item_per_column: IntProperty(name="Items per Column", get=get_auto_item_per_column, set=set_auto_item_per_column)
    auto_columns: CollectionProperty(type=MXD_Obj_CollT_UI_Collection_Column)
    # Custom
    custom_item_per_column: IntProperty(name="Items per Column", get=get_custom_item_per_column, set=set_custom_item_per_column)
    column_definition_type: EnumProperty(items=COLUMN_DEFINITION_TYPE, default='CUSTOM')
    custom_columns: CollectionProperty(type=MXD_Obj_CollT_UI_Collection_Column)
    active_column_index: IntProperty()


class MXD_Obj_PointT_UI_Collection(MXD_Pref_UI_Collection):
    settings_basis: EnumProperty(items=(('GLOBAL', "Global", ""), ('LOCAL', "Local (Object)", "")))



classes = (
    MXD_Obj_CollT_UI_Collection_Column,
    MXD_Pref_UI_Collection,
    MXD_Obj_PointT_UI_Collection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
