import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty


def copy_properties(from_PropertyGroup, to_PropertyGroup):
    for prop in from_PropertyGroup.bl_rna.properties:
        identifier = prop.identifier
        if prop.identifier == "rna_type":
            continue

        fro = getattr(from_PropertyGroup, identifier)
        to = getattr(to_PropertyGroup, identifier)

        match prop.type:
            case 'POINTER':
                copy_properties(fro, to)
            case 'COLLECTION':
                to.clear()
                for i in fro:
                    copy_properties(i, to.add())
            case _:
                setattr(to_PropertyGroup, identifier, fro)


class MXD_CollT_Name(PropertyGroup):
    name: StringProperty(name="", default="Item")


classes = (
    MXD_CollT_Name,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
