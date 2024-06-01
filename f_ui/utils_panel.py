import bpy
from mathutils import Vector
from .layout.ui_panel_layout import PanelLayout
from .utils.utils import Attr_Holder, EventTypeIntercepter


class MXD_OT_Utils_Panel:
    def invoke_panel(self, context, event):
        self.cursor = Vector((event.mouse_region_x, event.mouse_region_y))
        self.attr_holder = Attr_Holder()
        self.moved = False

        if not hasattr(self, "handler"):
            context.window_manager.modal_handler_add(self)
            self.space_data = context.space_data.__class__
            self.handler = self.space_data.draw_handler_add(self.draw_panel, (), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def panel_listener(self, context, __event):
        """

        FLOW

        1) UI Elements are first made (instantiated) by calling draw_structure which is defined by user
        2) Elements' modal()) are called
        3) Elements' make() are called which realize what changes where made in modal() and prepare the elements for drawing
        4) Elements are drawn

        """
        context.area.tag_redraw()
        event = EventTypeIntercepter(__event)
        layout = PanelLayout(self, self.cursor)
        self.draw_structure(context, event, layout)

        if not self.moved:  # Make it so that cursor is at the center of the panel when spawned
            if layout.children:
                rightmost = max(layout.children, key=lambda child: child.origin.x + child.width)
                bottommost = min(layout.children, key=lambda child: child.origin.y - child.height)
                width = rightmost.origin.x + rightmost.width + layout.MARGIN - layout.origin.x
                height = layout.origin.y - bottommost.origin.y + bottommost.height + layout.MARGIN
                self.cursor.x -= width / 2
                self.cursor.y += height / 2

                self.moved = True
                layout = PanelLayout(self, self.cursor)
                self.draw_structure(context, event, layout)

        layout.call_modals(context, event)

        if layout.draw_again:
            layout = PanelLayout(self, self.cursor)
            self.draw_structure(context, event, layout)
            layout.call_modals(context, event)

        layout.make_elements()
        self.ui_layout = layout

        if event.handled:
            return {'RUNNING_MODAL'}
        
        match event.type:
            # case 'MOUSEMOVE':
            #     return {'PASS_THROUGH'}

            # case 'LEFTMOUSE' if event.value == 'PRESS':


            case 'RIGHTMOUSE' | 'ESC' if event.value == 'PRESS':
                self.clean()
                return {'CANCELLED'}
            
            # case _ as e if 'MOUSE' in e:
            #     return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def clean(self):
        self.space_data.draw_handler_remove(self.handler, 'WINDOW')
        bpy.context.window.cursor_modal_restore()

    invoke = invoke_panel
    modal = panel_listener

    def draw_panel(self):
        self.ui_layout.draw()
