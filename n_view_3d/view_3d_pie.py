import bpy
from bpy.types import Menu


class MXD_MT_PIE_ViewportDisplay(Menu):
    bl_label = "Viewport Display"

    def draw(self, context):
        space = context.space_data
        show_gizmo = space.show_gizmo
        show_overlay = space.overlay.show_overlays
        match space.shading.type:
            case 'WIREFRAME':
                shading_icon = 'SHADING_WIRE'
            case 'SOLID':
                shading_icon = 'SHADING_SOLID'
            case 'MATERIAL':
                shading_icon = 'SHADING_TEXTURE'
            case 'RENDERED':
                shading_icon = 'SHADING_RENDERED'

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.call_panel", icon_value=space.icon_from_show_object_viewport,             # Left
                     text="View Object Types").name = "VIEW3D_PT_object_type_visibility"
        pie.operator("view3d.toggle_studio_light", text="Toggle Studio Light", icon='BLANK1')      # Right
        pie.operator("wm.call_menu_pie", text="Show ---",                                          # Bottom
                     icon='ADD').name = "MXD_MT_PIE_Show"
        pie.operator("view3d.toggle_overlays", depress=(show_overlay), text="Show Overlays",       # Top
                     icon='CHECKBOX_HLT' if show_overlay else 'CHECKBOX_DEHLT').mode = 'OVERLAYS'
        pie.operator("view3d.toggle_overlays", depress=(show_gizmo), text="Show Gizmo",            # Top_left
                     icon='CHECKBOX_HLT' if show_gizmo else 'CHECKBOX_DEHLT').mode = 'GIZMO'
        pie.operator("wm.call_panel", icon=shading_icon,                                           # Top_right
                     text="Viewport Shading").name = "VIEW3D_PT_shading"
        pie.operator("wm.call_panel", icon='BLANK1',                                               # Bottom_left
                     text="Object Viewport Display").name = "OBJECT_PT_display"
        if (obj := context.object):
            if obj.type == 'ARMATURE':
                pie.operator("wm.call_panel", text="Armature Viewport Display",                    # Bottom_right
                             icon='BLANK1').name = "MXD_DATA_PT_display"
            else:
                match context.mode:
                    case 'OBJECT':
                        pie.operator("shade.smooth", icon='BLANK1').mode = 'OBJECT'                        
                    case 'EDIT_MESH' | 'EDIT_CURVE':
                        pie.operator("shade.smooth", icon='BLANK1').mode = 'NON_OBJ'


class MXD_MT_PIE_Show(Menu):
    bl_label = ""

    def draw(self, context):
        overlay = context.space_data.overlay
        show_annotation = overlay.show_annotation
        show_bones = overlay.show_bones
        show_outline_selected = overlay.show_outline_selected
        show_wireframe = overlay.show_wireframes
        show_face_orientation = overlay.show_face_orientation
        show_backface_culling = context.space_data.shading.show_backface_culling

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("wm.context_toggle", depress=(show_annotation),                                  # Left
                     icon='CHECKBOX_HLT' if show_annotation else 'CHECKBOX_DEHLT',
                     text="Show Annotations").data_path = "space_data.overlay.show_annotation"
        pie.operator("wm.context_toggle", depress=(show_bones),                                       # Right
                     icon='CHECKBOX_HLT' if show_bones else 'CHECKBOX_DEHLT',
                     text="Show Bones").data_path = "space_data.overlay.show_bones"
        pie.operator("wm.context_toggle", depress=(show_backface_culling),                            # Bottom
                     icon='CHECKBOX_HLT' if show_backface_culling else 'CHECKBOX_DEHLT',
                     text="Backface Culling").data_path = "space_data.shading.show_backface_culling"
        pie.separator()  # Top
        pie.operator("wm.context_toggle", depress=(show_wireframe),                                   # Top_left
                     icon='CHECKBOX_HLT' if show_wireframe else 'CHECKBOX_DEHLT',
                     text="Wireframe").data_path = "space_data.overlay.show_wireframes"
        pie.operator("wm.context_toggle", depress=(show_face_orientation),                            # Top_right
                     icon='CHECKBOX_HLT' if show_face_orientation else 'CHECKBOX_DEHLT',
                     text="Face Orientation").data_path = "space_data.overlay.show_face_orientation"
        pie.separator()  # Bottom_left
        pie.operator("wm.context_toggle", depress=(show_outline_selected),                            # Bottom_right
                     icon='CHECKBOX_HLT' if show_outline_selected else 'CHECKBOX_DEHLT',
                     text="Outline Selected").data_path = "space_data.overlay.show_outline_selected"


class MXD_MT_PIE_AlignViewToActive(Menu):
    bl_label = 'Align View to Active'

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("view3d.view_axis", text="Left", icon='TRIA_LEFT')    # Left
        op.type = 'LEFT'
        op.align_active = True
        op = pie.operator("view3d.view_axis", text="Right", icon='TRIA_RIGHT')  # Right
        op.type = 'RIGHT'
        op.align_active = True
        op = pie.operator("view3d.view_axis", text="Bottom", icon='TRIA_DOWN')  # Bottom
        op.type = 'BOTTOM'
        op.align_active = True
        op = pie.operator("view3d.view_axis", text="Top", icon='TRIA_UP')       # Top
        op.type = 'TOP'
        op.align_active = True
        op = pie.operator("view3d.view_axis", text="Front", icon='BLANK1')      # Top_left
        op.type = 'FRONT'
        op.align_active = True
        op = pie.operator("view3d.view_axis", text="Back", icon='BLANK1')       # Top_right
        op.type = 'BACK'
        op.align_active = True
        pie.separator()  # Bottom_left
        pie.separator()  # Bottom_right


classes = (
    MXD_MT_PIE_ViewportDisplay,
    MXD_MT_PIE_Show,
    MXD_MT_PIE_AlignViewToActive,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
