import bpy
from bpy.types import Operator, Panel, UILayout, UIList
from ...f_ui.utils_panel import MXD_OT_Utils_Panel
from .bone_collections_op import Base_BoneCollectionsOps


class MXD_OT_Armature_BoneCollectionPanel(MXD_OT_Utils_Panel, Operator):
    bl_idname = "bone_collections_panel.invoke"
    bl_label = "Bone Collections"
    bl_options = {'REGISTER', 'INTERNAL'}
    add_mode = 'OBJECT'

    @classmethod
    def poll(cls, context):
        return Base_BoneCollectionsOps.poll_check_for_armature(cls, context)

    def invoke(self, context, event):
        for obj in {context.object, *context.selected_objects}:
            if obj.type == 'ARMATURE':
                self.object_name = obj.name  # Used .name since there is a operator that uses undo (would produce ReferenceError upon undo if only obj)
                break
        self.collection_pref_panel = MXD_PT_BoneCollectionProperties
        return super().invoke(context, event)

    def draw_structure(self, context, event, layout):
        layout.icon_scale = 0.8

        collections = bpy.data.objects[self.object_name].data.collections

        ui_coll = layout.collection("bone_collection", collections, self.draw_collection_item)
        layout.flow(horizontal=True)

        layout.icon_scale = 0.6
        add = layout.operator("armature.collection_add", label="", icon='ADD')
        layout.flow(vertical=True)
        layout.operator("armature.collection_remove", label="", icon='REMOVE').snap_to(add, 'BOTTOM')

        if collections.active:
            layout.icon_scale = 1
            up = layout.operator("armature.collection_move", label="", icon='TRIA_UP')
            up.prop.direction = 'UP'
            down = layout.operator("armature.collection_move", label="", icon='TRIA_DOWN')
            down.prop.direction = 'DOWN'
            down.snap_to(up, 'BOTTOM')

            layout.current_element = ui_coll
            layout.text_alignment = layout.text_alignment.center
            with layout.HorizontalSpacingManager() as hsm:
                hsm.operator("armature.collection_assign", label="Assign")
                hsm.operator("armature.collection_unassign", label="Remove")
                hsm.separator()
                hsm.operator("armature.collection_select", label="Select")
                hsm.operator("armature.collection_deselect", label="Deselect")

    def draw_collection_item(self, layout, collection, item):
        # TODO: read double clicks, time.time()
        ...
        if collection.active == item:
            layout.text(item, "name")
        else:
            layout.label(item.name)

        ui_bcoll = bpy.context.preferences.addons[__package__.partition(".")[0]].preferences.ui_bone_collections

        if ui_bcoll.show_lock:
            layout.collection_prop(collection, item, "MixedPie.locked", emboss=False, icon='LOCKED' if item.MixedPie.locked else 'UNLOCKED')
        layout.collection_prop(collection, item, "is_visible", emboss=False, icon='HIDE_OFF' if item.is_visible else 'HIDE_ON')
        if ui_bcoll.show_solo:
            layout.collection_prop(collection, item, "is_solo", emboss=False, icon='SOLO_ON' if item.is_solo else 'SOLO_OFF')


class MXD_UL_Column(UIList):
    def draw_item(self, context, layout: UILayout, data, item, icon, active_data, active_property, index):
        layout.prop(item, "name", emboss=False)
        row = layout.row()
        row.alignment = 'RIGHT'
        row.enabled = False
        count = item.item_count
        row.label(text=f"{count} item{'s' if count > 1 else ''}  ")


class MXD_UL_Item(UIList):
    def draw_item(self, context, layout: UILayout, data, item, icon, active_data, active_property, index):
        layout.prop(item, "name", emboss=False)


class MXD_PT_BoneCollectionProperties(Panel):
    bl_label = "Bone Collection Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 12

        pref = context.preferences.addons[__package__.partition(".")[0]].preferences
        ui_bcoll = pref.ui_bone_collections

        box = layout.box()
        row = box.row()
        row.prop(ui_bcoll, "is_expanded", emboss=False, icon='DOWNARROW_HLT' if ui_bcoll.is_expanded else 'RIGHTARROW')
        row.label(text="Bone Collection Properties")
        if ui_bcoll.is_expanded:
            col = box.column(align=True)
            row = col.row()
            row.label(icon='BLANK1')
            row.prop(ui_bcoll, "show_lock")

            row = col.row()
            row.label(icon='BLANK1')            
            row.prop(ui_bcoll, "show_solo")

        if not hasattr(self, "current_properties"):
            return
        current_properties = self.current_properties

        layout.label(text="Settings Basis")
        layout.prop(current_properties, "settings_basis", expand=True)

        def draw_settings(settings_basis, path):
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Column Definition Type")
            col.separator(factor=0.5)
            col.row().prop(settings_basis, "column_definition_type", expand=True)

            if settings_basis.column_definition_type == 'AUTOMATIC':
                col = box.column(align=True)
                col.prop(settings_basis, "max_column_amount")
                col.prop(settings_basis, "auto_item_per_column")
            else:
                col = box.column(align=True)
                col.label(text="Columns")
                col.separator(factor=0.5)
                row = col.row()
                row.template_list("MXD_UL_Column", "", settings_basis, "custom_columns", settings_basis, "active_column_index", sort_lock=True)
                index_path = path + ".active_column_index"
                columns_path = path + ".custom_columns"
                custom_columns = settings_basis.custom_columns
                active_column_index = settings_basis.active_column_index
                active_column = custom_columns[active_column_index]

                col = row.column(align=True)
                op = col.operator("utils.modify_collection_item", icon='ADD')
                op.operation = 'ADD'
                op.collection = columns_path
                op.index = active_column_index

                if len(custom_columns) > 0:
                    row = col.row()
                    row.enabled = (active_column.name != "Uncategorized" or
                                len([col.name for col in custom_columns if col.name == "Uncategorized"]) > 1)  # If there are many "Uncategorized", enable remove
                    op = row.operator("utils.modify_collection_item", icon='REMOVE')
                    op.operation = 'REMOVE'
                    op.collection = columns_path
                    op.index = active_column_index
                    op.index_path = index_path

                if len(custom_columns) > 1:
                    col.separator()

                    op = col.operator("utils.modify_collection_item", icon='TRIA_UP')
                    op.operation = 'MOVE_UP'
                    op.collection = columns_path
                    op.index = active_column_index
                    op.index_path = index_path

                    op = col.operator("utils.modify_collection_item", icon='TRIA_DOWN')
                    op.operation = 'MOVE_DOWN'
                    op.collection = columns_path
                    op.index = active_column_index
                    op.index_path = index_path

                if not custom_columns:
                    return
                if active_column_index > len(custom_columns) - 1:
                    return
                if active_column.name == "Uncategorized":
                    return

                col = box.column(align=True)
                col.label(text="Items")
                col.separator(factor=0.5)
                row = col.row()
                row.template_list("MXD_UL_Item", "", active_column, "items", active_column, "active_item_index", sort_lock=True)
                index_path = path + f"[{active_column_index}].active_item_index"
                items_path = path + f"[{active_column_index}].items"
                active_item_index = active_column.active_item_index

                col = row.column(align=True)
                op = col.operator("utils.modify_collection_item", icon='ADD')
                op.operation = 'ADD'
                op.collection = items_path
                op.index = active_item_index

                if len(active_column.items) > 0:
                    op = col.operator("utils.modify_collection_item", icon='REMOVE')
                    op.operation = 'REMOVE'
                    op.collection = items_path
                    op.index = active_item_index
                    op.index_path = index_path

                if len(active_column.items) > 1:
                    col.separator()

                    op = col.operator("utils.modify_collection_item", icon='TRIA_UP')
                    op.operation = 'MOVE_UP'
                    op.collection = items_path
                    op.index = active_item_index
                    op.index_path = index_path

                    op = col.operator("utils.modify_collection_item", icon='TRIA_DOWN')
                    op.operation = 'MOVE_DOWN'
                    op.collection = items_path
                    op.index = active_item_index
                    op.index_path = index_path

                col.separator()
                op = col.operator("bone_collections.select_items_for_column", icon='COLLECTION_NEW')
                op.collection = items_path

        if current_properties.settings_basis == 'LOCAL':
            path = repr(current_properties)
            draw_settings(current_properties, path)
        else:
            path = f"bpy.context.preferences.addons[__package__.partition('.')[0]].preferences.ui_collections.list[{self.current_collection_identifier}]"
            draw_settings(pref.ui_collections.list[self.current_collection_identifier], path)


classes = (
    MXD_OT_Armature_BoneCollectionPanel,
    MXD_UL_Column,
    MXD_UL_Item,
    MXD_PT_BoneCollectionProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
