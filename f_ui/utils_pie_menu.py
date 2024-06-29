from mathutils import Vector
from .layout.ui_pie_menu import PieMenuLayout
from .utils.utils import Attr_Holder, EventTypeIntercepter


class MXD_OT_Utils_PieMenu:
    # TODO: Update docs
    # """
    # Use add_button
    # Define a self.button_effects(context, button_id)
    # Call self.invoke_pie_menu(context, event) in invoke()
    # """
    # TODO: Add description

    def invoke_pie_menu(self, context, event):
        self.cursor = Vector((event.mouse_region_x, event.mouse_region_y))
        self.origin = Vector((event.mouse_region_x, event.mouse_region_y))
        self.attr_holder = Attr_Holder()

        if not hasattr(self, "handler"):
            context.window_manager.modal_handler_add(self)
            self.space_data = context.space_data.__class__
            self.handler = self.space_data.draw_handler_add(self.draw_pie, (), 'WINDOW', 'POST_PIXEL')
            self.pie_subclassed = False
        else:
            self.pie_subclassed = True
            # TODO: Do something with using these in middle of another modal, cause it would quit all
            # TODO: Put op bl_label at center

        return {'RUNNING_MODAL'}

    def pie_listener(self, context, __event):
        context.area.tag_redraw()
        layout = PieMenuLayout(self, self.cursor)
        event = EventTypeIntercepter(__event, layout.ui_scale, self.attr_holder)

        self.ui_layout = layout
        self.draw_structure(context, event, layout)
        layout.call_modals(context, event)
        layout.make_elements()

        match event.type:
            case 'LEFTMOUSE' if event.value == 'PRESS':
                self.space_data.draw_handler_remove(self.handler, 'WINDOW')
                for button in layout.buttons:
                    if button.active:
                        self.button_effects(context, button)
                        return {'FINISHED'} if not self.pie_subclassed else None
                else:
                    return {'CANCELLED'} if not self.pie_subclassed else None

            case 'RIGHTMOUSE' | 'ESC' if event.value == 'PRESS':
                self.space_data.draw_handler_remove(self.handler, 'WINDOW')
                return {'CANCELLED'} if not self.pie_subclassed else None

        return {'RUNNING_MODAL'}

    modal = pie_listener

    def draw_pie(self):
        self.ui_layout.draw()
