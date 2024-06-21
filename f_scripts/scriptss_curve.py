import bpy
from bpy.types import Context, Operator


class Duplicate_and_Convert_Curves_to_Mesh:
    """ Also transfer subdivision to converted mesh """

    @classmethod
    def find_layer_collection_recursively(cls, layer_coll, target_name):
        if layer_coll.name == target_name:
            return layer_coll
        for child in layer_coll.children:
            if (target := cls.find_layer_collection_recursively(child, target_name)):
                return target

    @classmethod
    def execute(cls, operator: Operator, context: Context):

        pre_select_state = context.active_object.select_get()
        context.active_object.select_set(True)
        curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        
        if not curves:
            context.active_object.select_set(pre_select_state)
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            if obj.type != 'CURVE':
                obj.select_set(False)
        
        if context.active_object.type != 'CURVE':
            context.view_layer.objects.active = curves[0]

        parent_collection = context.object.users_collection[0]
        if not (new_collection := parent_collection.children.get(f"c_{parent_collection.name}")):
            new_collection = bpy.data.collections.new(f"c_{parent_collection.name}")
            parent_collection.children.link(new_collection)
        cls.find_layer_collection_recursively(context.view_layer.layer_collection, new_collection.name).hide_viewport = True

        bpy.ops.object.duplicate()
        # Duplicating should have worked on all selected objects, original selections are unselected, and the new selections preserve the order before
        bpy.ops.object.convert()

        for curve, dup_mesh in zip(curves, context.selected_objects):
            name = curve.name
            curve.name = f"c_{name}"
            dup_mesh.name = name

            parent_collection.objects.unlink(curve)
            new_collection.objects.link(curve)

            for mod in curve.modifiers:
                if mod.type == 'SUBSURF':
                    new_mod = dup_mesh.modifiers.new("", 'SUBSURF')

                    for prop in mod.bl_rna.properties:
                        if not prop.is_readonly:
                            setattr(new_mod, prop.identifier, getattr(mod, prop.identifier))

        operator.report({'INFO'}, f"Duplicated and Converted {len(curves)} curve{'s' if len(curves) > 1 else ''} to Mesh.")
