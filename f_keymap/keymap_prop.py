import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    IntProperty,
    StringProperty,
)


class CT_KeymapShowExpanded(PropertyGroup):
    show_expanded: BoolProperty(name="")


class CT_KeymapChanges(PropertyGroup):
    km_name: StringProperty()
    kmi_id: IntProperty()

    def set(self, km_name, kmi_id):
        self.km_name = km_name
        self.kmi_id = kmi_id


class Keymap(PropertyGroup):
    expanded: BoolProperty(name="")
    group_relation_or_mode: BoolProperty(name="", description="Show keymap groups by relation or by mode context")

    set_changes: BoolProperty()
    kmi_changes: CollectionProperty(type=CT_KeymapChanges)
    changes_expanded: BoolProperty(name="")

    view_3d_w_prior_state: BoolProperty(default=True)
    uv_editor_w_prior_state: BoolProperty(default=True)
    sculpt_w_prior_state: BoolProperty()


classes = (
    CT_KeymapShowExpanded,
    CT_KeymapChanges,
    Keymap,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
