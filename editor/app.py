import math
import sys

import pygame
from pygame.locals import (
    DOUBLEBUF,
    KEYDOWN,
    KMOD_CTRL,
    KMOD_SHIFT,
    K_0,
    K_1,
    K_3,
    K_5,
    K_7,
    K_BACKSPACE,
    K_c,
    K_DELETE,
    K_ESCAPE,
    K_g,
    K_q,
    K_r,
    K_RETURN,
    K_s,
    K_TAB,
    K_v,
    K_x,
    K_y,
    K_z,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    MOUSEMOTION,
    OPENGL,
    QUIT,
)
from OpenGL.GL import (
    GL_BACK,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINE_LOOP,
    GL_LINE_SMOOTH,
    GL_LINE_SMOOTH_HINT,
    GL_MODELVIEW,
    GL_NICEST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_SMOOTH,
    GL_SRC_ALPHA,
    glBegin,
    glBlendFunc,
    glClear,
    glClearColor,
    glColor4f,
    glCullFace,
    glDisable,
    glEnable,
    glEnd,
    glHint,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glShadeModel,
    glVertex3f,
    glViewport,
)
from OpenGL.GLU import gluLookAt, gluPerspective

from editor.camera import Camera
from editor.constants import (
    ACCENT,
    AXIS_LABEL_COLORS,
    AXIS_VECTORS,
    CUBE_COLOR,
    DANGER,
    END_COLOR,
    HEADER_H,
    KILL_GLOW,
    KILL_RED,
    SELECT_COL,
    SIDEBAR_W,
    START_COLOR,
    SUCCESS,
    TARGET_FPS,
    TOOL_ICONS,
    TXT_DIM,
    TXT_MAIN,
    TXT_MUTED,
    TXT_WHITE,
    UI_BORDER,
    UI_DIVIDER,
    UI_HEADER,
    UI_MENU,
    UI_MENU_BD,
    UI_MENU_HOVER,
    UI_PANEL,
    UI_PANEL_HI,
    UI_SIDEBAR,
    UI_TOOLBAR,
    UI_TOOLBAR_BD,
    VP_BG,
    WARN,
    WINDOW_H,
    WINDOW_W,
)
from editor.context_menu import ContextMenu, ITEM_H, MENU_W, PAD_Y
from editor.export import ExportDialog
from editor.gizmo import draw_gizmo, pick_gizmo_axis
from editor.history import History
from editor.icons import draw_icon
from editor.level import Level
from editor.projection import (
    closest_t_on_axis,
    project,
    ray_intersect_plane_y,
    screen_to_ray,
)
from editor.rendering import (
    build_floor_list,
    call_floor_list,
    draw_cylinder_boundary,
    draw_cube,
    draw_shape,
)
from editor.text_cache import text_width
from editor.ui import (
    button as ui_button,
    fill as ui_fill,
    hit as ui_hit,
    hline as ui_hline,
    section as ui_section,
    text as ui_text,
    tooltip as ui_tooltip,
)


ICON_BTN = 30
ICON_GAP = 4
TOOLBAR_X = 8
TOOLBAR_Y = HEADER_H + 8


class LevelEditor:
    def __init__(self):
        pygame.init()
        self.width, self.height = WINDOW_W, WINDOW_H
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            DOUBLEBUF | OPENGL | pygame.RESIZABLE,
        )
        pygame.display.set_caption("Tower Level Editor")
        self.clock = pygame.time.Clock()

        self.f_title = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.f_hd = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.f_body = pygame.font.SysFont("Segoe UI", 13)
        self.f_small = pygame.font.SysFont("Segoe UI", 11)
        self.f_btn = pygame.font.SysFont("Segoe UI", 13)
        self.f_key = pygame.font.SysFont("Consolas", 11, bold=True)
        self.f_num = pygame.font.SysFont("Consolas", 12)
        self.f_big = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.f_dlg = pygame.font.SysFont("Segoe UI", 14)

        self.level = Level()
        self.camera = Camera()
        self.history = History()
        self.export_dialog = ExportDialog()
        self.context_menu = ContextMenu()

        self.selected = None
        self.tool = "move"
        self.axis = "xyz"
        self.clipboard = None

        self.mouse_x, self.mouse_y = 0, 0
        self.hovered_axis = None
        self.active_axis = None
        self.drag_mode = None
        self.drag_last = (0, 0)
        self.drag_button_pos = (0, 0)
        self.drag_moved = False

        self.drag_start_pos = None
        self.drag_start_rot = None
        self.drag_start_scl = None
        self.drag_start_t = 0.0
        self.drag_start_mx = 0

        self.hovered_tool = None
        self.hovered_menu_item = None

        self.running = True

        self._setup_opengl()
        self.floor_list = build_floor_list()
        self.history.snapshot(self.level)

    def _setup_opengl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glClearColor(*VP_BG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glShadeModel(GL_SMOOTH)

    def viewport_w(self):
        return self.width - SIDEBAR_W

    def get_selected(self):
        if self.selected is None:
            return None
        if 0 <= self.selected < len(self.level.objects):
            return self.level.objects[self.selected]
        return None

    def _push_undo(self):
        self.history.snapshot(self.level)

    def _set_3d_matrices(self):
        vw = self.viewport_w()
        vh = self.height - HEADER_H
        glViewport(0, 0, vw, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            self.camera.fov,
            (vw / vh) if vh else 1.0,
            self.camera.near,
            self.camera.far,
        )
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        p = self.camera.position()
        t = self.camera.target
        gluLookAt(p[0], p[1], p[2], t[0], t[1], t[2], 0.0, 1.0, 0.0)

    def raycast_ground(self, mx, my):
        ro, rd = screen_to_ray(mx, my, self.camera, self.viewport_w(), self.height)
        return ray_intersect_plane_y(ro, rd, 0.0)

    def pick_object(self, mx, my):
        vw, vh = self.viewport_w(), self.height
        best_index = None
        best_d = 55.0
        for i, obj in enumerate(self.level.objects):
            p = project(obj.position, self.camera, vw, vh)
            if p is None:
                continue
            d = math.hypot(p[0] - mx, p[1] - my)
            thr = 25.0 + max(obj.scale) * 0.4
            if thr > 90.0:
                thr = 90.0
            if d < best_d and d < thr:
                best_d = d
                best_index = i
        return best_index

    def _pick_gizmo(self, mx, my):
        if mx >= self.viewport_w():
            return None
        obj = self.get_selected()
        return pick_gizmo_axis(
            obj, self.tool, mx, my,
            self.camera, self.viewport_w(), self.height,
        )

    def _toolbar_button_at(self, mx, my):
        if my < TOOLBAR_Y or my > TOOLBAR_Y + ICON_BTN:
            return None
        for i, (tool, _label, _key) in enumerate(TOOL_ICONS):
            x = TOOLBAR_X + i * (ICON_BTN + ICON_GAP)
            if x <= mx <= x + ICON_BTN:
                return tool
        return None

    def _toolbar_rect(self, tool):
        for i, (t, _l, _k) in enumerate(TOOL_ICONS):
            if t == tool:
                x = TOOLBAR_X + i * (ICON_BTN + ICON_GAP)
                return (x, TOOLBAR_Y, ICON_BTN, ICON_BTN)
        return None

    def _on_key_down(self, ev):
        if self.export_dialog.active:
            self._on_dialog_key(ev)
            return

        k = ev.key
        mods = pygame.key.get_mods()
        ctrl = bool(mods & KMOD_CTRL)
        shift = bool(mods & KMOD_SHIFT)

        if k == K_ESCAPE:
            if self.context_menu.active:
                self.context_menu.close()
            else:
                self.running = False
        elif ctrl and k == K_z:
            if shift:
                self.redo()
            else:
                self.undo()
        elif ctrl and k == K_y:
            self.redo()
        elif ctrl and k == K_c:
            self.copy_selected()
        elif ctrl and k == K_v:
            self.paste_clipboard()
        elif ctrl and k == K_s:
            self.open_export_dialog()
        elif k == K_TAB:
            order = ("move", "scale", "rotate", "select")
            self.tool = order[(order.index(self.tool) + 1) % 4]
        elif k == K_g:
            self.tool = "move"
        elif k == K_r:
            self.tool = "rotate"
        elif k == K_s and not ctrl:
            self.tool = "scale"
        elif k == K_q:
            self.tool = "select"
        elif k == K_DELETE:
            self.delete_selected()
        elif k == K_x:
            self.axis = "x"
        elif k == K_y:
            self.axis = "y"
        elif k == K_z:
            self.axis = "z"
        elif k == K_0:
            self.axis = "xyz"
        elif k == K_1:
            self.camera.set_view("front")
        elif k == K_3:
            self.camera.set_view("right")
        elif k == K_7:
            self.camera.set_view("top")
        elif k == K_5:
            self.camera.set_view("persp")

    def _on_dialog_key(self, ev):
        k = ev.key
        if k == K_ESCAPE:
            self.export_dialog.close()
        elif k == K_RETURN:
            self.export_dialog.submit(self.level.height, self.level.objects)
        elif k == K_TAB:
            self.export_dialog.toggle_field()
        elif k == K_BACKSPACE:
            self.export_dialog.backspace()

    def _on_text_input(self, ev):
        if self.export_dialog.active:
            self.export_dialog.append(ev.text)

    def _on_mouse_down(self, ev):
        mx, my = ev.pos
        self.mouse_x, self.mouse_y = mx, my
        self.drag_last = ev.pos
        self.drag_button_pos = ev.pos
        self.drag_moved = False

        if self.export_dialog.active:
            self._handle_dialog_click(mx, my, ev.button)
            return

        if self.context_menu.active:
            idx = self.context_menu.hit_test(mx, my)
            if idx is not None and idx >= 0:
                self._spawn_from_menu(idx)
                self.context_menu.close()
                return
            self.context_menu.close()
            return

        in_sidebar = mx >= self.viewport_w()
        in_header = my < HEADER_H

        if in_header:
            return

        if ev.button == 1:
            toolbar_tool = self._toolbar_button_at(mx, my)
            if toolbar_tool is not None and not in_sidebar:
                self.tool = toolbar_tool
                return

            if in_sidebar:
                self._handle_sidebar_click(mx, my)
                return

            axis = self._pick_gizmo(mx, my)
            if axis is not None:
                self._begin_axis_drag(axis, mx, my)
                return

            idx = self.pick_object(mx, my)
            if idx is not None:
                self.selected = idx
                return

            self.selected = None
            self.drag_mode = "orbit"

        elif ev.button == 2:
            mods = pygame.key.get_mods()
            self.drag_mode = "pan" if (mods & KMOD_SHIFT) else "orbit"

        elif ev.button == 3:
            if not in_sidebar:
                self.drag_mode = "rmb_undecided"

        elif ev.button == 4:
            self.camera.zoom(-18.0)
        elif ev.button == 5:
            self.camera.zoom(18.0)

    def _on_mouse_up(self, ev):
        if ev.button == 3 and self.drag_mode == "rmb_undecided" and not self.drag_moved:
            mx, my = ev.pos
            if mx < self.viewport_w() and my >= HEADER_H:
                world = self.raycast_ground(mx, my)
                if world is None:
                    t = self.camera.target
                    world = (t[0], 0.0, t[2])
                self.context_menu.open(mx, my, world)

        if ev.button in (1, 2, 3):
            self.drag_mode = None
            self.active_axis = None

    def _on_mouse_motion(self, ev):
        mx, my = ev.pos
        self.mouse_x, self.mouse_y = mx, my

        if self.context_menu.active:
            self.hovered_menu_item = self.context_menu.hit_test(mx, my)
            if self.hovered_menu_item is not None and self.hovered_menu_item < 0:
                self.hovered_menu_item = None
        else:
            self.hovered_menu_item = None

        self.hovered_tool = None
        if my >= HEADER_H:
            t = self._toolbar_button_at(mx, my)
            if t is not None:
                self.hovered_tool = t

        if self.drag_mode is None:
            self.hovered_axis = self._pick_gizmo(mx, my)
            return

        dx = mx - self.drag_last[0]
        dy = my - self.drag_last[1]
        self.drag_last = ev.pos

        if abs(mx - self.drag_button_pos[0]) > 3 or abs(my - self.drag_button_pos[1]) > 3:
            self.drag_moved = True

        if self.drag_mode == "orbit":
            self.camera.orbit(dx, dy)
        elif self.drag_mode == "pan":
            self.camera.pan(dx, dy)
        elif self.drag_mode == "rmb_undecided":
            if self.drag_moved:
                self.drag_mode = "pan"
                self.camera.pan(dx, dy)
        elif self.drag_mode == "axis":
            self._update_axis_drag(mx, my)

    def _begin_axis_drag(self, axis, mx, my):
        obj = self.get_selected()
        if obj is None:
            return
        self._push_undo()
        self.drag_mode = "axis"
        self.active_axis = axis
        self.drag_start_pos = list(obj.position)
        self.drag_start_rot = list(obj.rotation)
        self.drag_start_scl = list(obj.scale)
        self.drag_start_mx = mx
        ro, rd = screen_to_ray(mx, my, self.camera, self.viewport_w(), self.height)
        self.drag_start_t = closest_t_on_axis(ro, rd, self.drag_start_pos, AXIS_VECTORS[axis])

    def _update_axis_drag(self, mx, my):
        obj = self.get_selected()
        if obj is None or self.active_axis is None:
            return
        axis = self.active_axis
        ro, rd = screen_to_ray(mx, my, self.camera, self.viewport_w(), self.height)
        t = closest_t_on_axis(ro, rd, self.drag_start_pos, AXIS_VECTORS[axis])
        delta = t - self.drag_start_t

        if self.tool == "move":
            obj.position[axis] = self.drag_start_pos[axis] + delta
            self.level.clamp_position(obj)
        elif self.tool == "scale":
            obj.scale[axis] = max(0.5, self.drag_start_scl[axis] + delta)
            self.level.clamp_position(obj)
        elif self.tool == "rotate":
            dx_px = mx - self.drag_start_mx
            obj.rotation[axis] = self.drag_start_rot[axis] + dx_px * 0.5

    def undo(self):
        if self.history.undo(self.level):
            self.selected = None

    def redo(self):
        if self.history.redo(self.level):
            self.selected = None

    def copy_selected(self):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        self.clipboard = obj.clone()

    def paste_clipboard(self):
        if self.clipboard is None:
            return
        self._push_undo()
        clone = self.clipboard.clone()
        prefix = {
            "box": "Box",
            "sphere": "Sphere",
            "cylinder": "Cylinder",
            "cone": "Cone",
            "wedge": "Wedge",
            "kill": "Kill",
        }.get(clone.kind, "Part")
        clone.name = self.level._next_name(prefix)
        self.level.clamp_position(clone)
        self.level.objects.append(clone)
        self.selected = len(self.level.objects) - 1

    def delete_selected(self):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        self._push_undo()
        del self.level.objects[self.selected]
        if self.level.objects:
            self.selected = min(self.selected, len(self.level.objects) - 1)
        else:
            self.selected = None

    def _spawn_from_menu(self, index):
        kind, _label = self.context_menu.items[index]
        world = self.context_menu.world_pos
        if world is None:
            t = self.camera.target
            world = (t[0], 0.0, t[2])
        x, z = self.level.clamp_new_position(world[0], world[2])
        self._push_undo()
        obj = self.level.add_shape(kind, [x, None, z])
        self.selected = len(self.level.objects) - 1

    def _handle_sidebar_click(self, mx, my):
        lx = mx - self.viewport_w()
        pad = 16
        inner_w = SIDEBAR_W - 2 * pad
        half_w = (inner_w - 10) // 2

        def in_row(y0, y1, x0, x1):
            return y0 <= my <= y1 and x0 <= lx <= x1

        if in_row(80, 112, pad, pad + half_w):
            self.set_tool("move")
            return
        if in_row(80, 112, pad + half_w + 10, pad + inner_w):
            self.set_tool("scale")
            return
        if in_row(120, 152, pad, pad + half_w):
            self.set_tool("rotate")
            return
        if in_row(120, 152, pad + half_w + 10, pad + inner_w):
            self.set_tool("select")
            return

        if in_row(192, 224, pad, pad + inner_w):
            self.open_export_dialog()
            return

        if in_row(276, 308, pad + 6, pad + 40):
            self._push_undo()
            self.set_height_delta(-Level.HEIGHT_STEP)
            return
        if in_row(276, 308, pad + inner_w - 40, pad + inner_w - 6):
            self._push_undo()
            self.set_height_delta(Level.HEIGHT_STEP)
            return

        ax_w, ax_gap = 64, 8
        for i, key in enumerate(("x", "y", "z", "xyz")):
            bx = pad + i * (ax_w + ax_gap)
            if in_row(344, 376, bx, bx + ax_w):
                self.set_axis(key)
                return

    def _dialog_rects(self):
        panel_w = 460
        panel_h = 250
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        field_w = panel_w - 40
        field_h = 34
        level_rect = (px + 20, py + 78, field_w, field_h)
        author_rect = (px + 20, py + 138, field_w, field_h)
        btn_h = 32
        btn_w = 130
        cancel_rect = (px + 20, py + panel_h - 52, btn_w, btn_h)
        export_rect = (px + panel_w - 20 - btn_w, py + panel_h - 52, btn_w, btn_h)
        return {
            "panel": (px, py, panel_w, panel_h),
            "level": level_rect,
            "author": author_rect,
            "cancel": cancel_rect,
            "export": export_rect,
        }

    def _handle_dialog_click(self, mx, my, button):
        if button != 1:
            return
        rects = self._dialog_rects()

        def inside(rect):
            x, y, w, h = rect
            return x <= mx <= x + w and y <= my <= y + h

        if inside(rects["level"]):
            self.export_dialog.field = "level"
            return
        if inside(rects["author"]):
            self.export_dialog.field = "author"
            return
        if inside(rects["cancel"]):
            self.export_dialog.close()
            return
        if inside(rects["export"]):
            self.export_dialog.submit(self.level.height, self.level.objects)
            return

        if not inside(rects["panel"]):
            self.export_dialog.close()

    def open_export_dialog(self):
        self.export_dialog.open()

    def set_height_delta(self, delta):
        self.level.set_height(self.level.height + delta)
        for obj in self.level.objects:
            self.level.clamp_position(obj)

    def set_axis(self, key):
        self.axis = key

    def set_tool(self, tool):
        self.tool = tool

    def render_3d(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._set_3d_matrices()

        call_floor_list(self.floor_list)
        draw_cylinder_boundary(Level.RADIUS, self.level.height)

        for i, obj in enumerate(self.level.objects):
            draw_shape(obj)

            if obj.kind == "kill":
                glDisable(GL_DEPTH_TEST)
                y = obj.position[1] + obj.scale[1] * 0.5 + 0.03
                hx = obj.scale[0] * 0.5 + 0.8
                hz = obj.scale[2] * 0.5 + 0.8
                cx, cz = obj.position[0], obj.position[2]
                glLineWidth(2.0)
                glColor4f(*KILL_GLOW)
                glBegin(GL_LINE_LOOP)
                glVertex3f(cx - hx, y, cz - hz)
                glVertex3f(cx + hx, y, cz - hz)
                glVertex3f(cx + hx, y, cz + hz)
                glVertex3f(cx - hx, y, cz + hz)
                glEnd()
                glEnable(GL_DEPTH_TEST)

        sel = self.get_selected()
        if sel is not None:
            glDisable(GL_DEPTH_TEST)
            draw_cube(
                sel.position,
                [sel.scale[0] + 0.6, sel.scale[1] + 0.6, sel.scale[2] + 0.6],
                sel.rotation,
                SELECT_COL,
                wireframe=True,
            )
            glEnable(GL_DEPTH_TEST)

        if sel is not None and self.tool != "select":
            draw_gizmo(sel, self.tool, self.hovered_axis, self.active_axis)

    def _text(self, s, x, y, color=TXT_MAIN, font=None):
        if font is None:
            font = self.f_body
        ui_text(s, x, y, color, font, self.height)

    def _fill(self, x, y, w, h, color, border=None, bw=1.0):
        ui_fill(x, y, w, h, color, border, bw)

    def _hline(self, x, y, w, color=UI_DIVIDER):
        ui_hline(x, y, w, color)

    def _section(self, x, y, w, label):
        ui_section(x, y, w, label, self.height, self.f_hd)

    def _button(self, x, y, w, h, label, key=None, active=False, accent=None):
        ui_button(
            x, y, w, h, label, self.height,
            key=key, active=active, accent=accent,
            mouse_x=self.mouse_x, mouse_y=self.mouse_y,
            font_body=self.f_btn, font_key=self.f_key,
        )

    def render_ui(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        vw = self.viewport_w()

        self._fill(vw, 0, SIDEBAR_W, self.height, UI_SIDEBAR)
        self._fill(vw, 0, 1, self.height, UI_BORDER)

        self._fill(0, 0, vw, HEADER_H, UI_HEADER)
        self._hline(0, HEADER_H, vw, UI_BORDER)
        self._text("Tower Editor", 12, 6, TXT_MAIN, self.f_title)
        self._text("|", 122, 7, TXT_MUTED, self.f_small)
        self._text("3D Viewport", 132, 7, TXT_DIM, self.f_small)

        stat_txt = (
            f"Objects: {len(self.level.objects)}    "
            f"H: {self.level.height:.0f}    "
            f"R: {Level.RADIUS:.0f}"
        )
        stw = text_width(stat_txt, TXT_DIM, self.f_small)
        self._text(stat_txt, vw - stw - 12, 7, TXT_DIM, self.f_small)

        self._render_toolbar()

        pad = 16
        x0 = vw + pad
        inner_w = SIDEBAR_W - 2 * pad
        half_w = (inner_w - 10) // 2

        self._text("LEVEL EDITOR", x0, 12, TXT_MAIN, self.f_big)
        self._text("Single-layer tower", x0, 32, TXT_MUTED, self.f_small)

        self._section(x0, 56, inner_w, "TOOLS")
        self._button(x0, 78, half_w, 32, "Move", key="G", active=self.tool == "move")
        self._button(x0 + half_w + 10, 78, half_w, 32, "Scale", key="S", active=self.tool == "scale")
        self._button(x0, 118, half_w, 32, "Rotate", key="R", active=self.tool == "rotate")
        self._button(x0 + half_w + 10, 118, half_w, 32, "Select", key="Q", active=self.tool == "select")

        self._section(x0, 168, inner_w, "FILE")
        self._button(x0, 190, inner_w, 32, "Export to JSON", key="+S", accent=SUCCESS)

        self._section(x0, 240, inner_w, "LEVEL HEIGHT")
        self._fill(x0, 260, inner_w, 36, UI_PANEL, UI_BORDER)
        self._button(x0 + 6, 264, 34, 28, "-")
        self._button(x0 + inner_w - 40, 264, 34, 28, "+")
        vstr = f"{self.level.height:.0f}"
        vw_ = text_width(vstr, TXT_MAIN, self.f_big)
        self._text(vstr, x0 + (inner_w - vw_) // 2, 268, TXT_MAIN, self.f_big)
        self._text("units", x0 + inner_w - 96, 271, TXT_MUTED, self.f_small)

        self._section(x0, 308, inner_w, "AXIS LOCK")
        ax_w, ax_gap = 64, 8
        for i, (label, key) in enumerate((("X", "x"), ("Y", "y"), ("Z", "z"), ("ALL", "xyz"))):
            bx = x0 + i * (ax_w + ax_gap)
            active = self.axis == key
            col = AXIS_LABEL_COLORS[key]
            hover = ui_hit(bx, 328, ax_w, 28, self.mouse_x, self.mouse_y)
            if active:
                bg = (0.28, 0.50, 0.78, 1.0)
                border, txt = bg, TXT_WHITE
            else:
                bg = (0.35, 0.35, 0.35, 1.0) if hover else (0.28, 0.28, 0.28, 1.0)
                border, txt = UI_BORDER, col
            self._fill(bx, 328, ax_w, 28, bg, border)
            tw_l = text_width(label, txt, self.f_btn)
            self._text(label, bx + (ax_w - tw_l) // 2,
                       328 + (28 - self.f_btn.get_height()) // 2, txt, self.f_btn)

        self._section(x0, 384, inner_w, "SELECTION")
        sel = self.get_selected()

        if sel is None:
            self._fill(x0, 406, inner_w, 54, UI_PANEL, UI_BORDER)
            self._text("Nothing selected", x0 + 12, 420, TXT_MUTED, self.f_body)
            self._text("Right-click to create a part",
                       x0 + 12, 440, TXT_MUTED, self.f_small)
        else:
            self._fill(x0, 406, inner_w, 28, UI_PANEL_HI, UI_BORDER)
            kind_col = {
                "box": CUBE_COLOR,
                "sphere": (0.60, 0.66, 0.74),
                "cylinder": (0.58, 0.63, 0.71),
                "cone": (0.62, 0.62, 0.68),
                "wedge": (0.56, 0.62, 0.70),
                "kill": KILL_RED,
                "start": START_COLOR,
                "end": END_COLOR,
            }.get(sel.kind, CUBE_COLOR)
            self._fill(x0 + 6, 412, 14, 16, kind_col, UI_BORDER)
            self._text(sel.name, x0 + 26, 411, TXT_MAIN, self.f_body)
            kind_s = sel.kind.upper()
            kw = text_width(kind_s, TXT_MUTED, self.f_small)
            self._text(kind_s, x0 + inner_w - kw - 10, 413, TXT_MUTED, self.f_small)

            y = 448

            def prop_row(label, vals, fmt="{:.2f}"):
                nonlocal y
                self._text(label, x0, y, TXT_DIM, self.f_small)
                y += 16
                col_w = inner_w // 3
                for i in range(3):
                    px = x0 + i * col_w
                    colr = AXIS_LABEL_COLORS[("x", "y", "z")[i]]
                    self._fill(
                        px, y, 16, 20,
                        (colr[0] * 0.32, colr[1] * 0.32, colr[2] * 0.32, 1.0),
                        (colr[0] * 0.6, colr[1] * 0.6, colr[2] * 0.6, 1.0),
                    )
                    self._text(("X", "Y", "Z")[i], px + 5, y + 3, colr, self.f_key)
                    self._text(fmt.format(vals[i]), px + 22, y + 3, TXT_MAIN, self.f_num)
                y += 28

            prop_row("Position", sel.position)
            prop_row("Size", sel.scale)
            prop_row("Rotation", sel.rotation, "{:.1f}deg")

        kh = self.height - 200
        self._section(x0, kh, inner_w, "KEYBINDS")

        bindings = (
            ("G/S/R/Q", "Tools"),
            ("X/Y/Z", "Axis lock"),
            ("0", "All axes"),
            ("1/3/7", "Views"),
            ("Ctrl+C/V", "Copy/Paste"),
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y", "Redo"),
            ("Ctrl+S", "Export"),
            ("Del", "Delete"),
            ("RMB", "Context menu"),
            ("MMB", "Orbit"),
            ("Shift+MMB", "Pan"),
            ("Wheel", "Zoom"),
        )
        yy = kh + 22
        col_w = inner_w // 2
        for i, (k, v) in enumerate(bindings):
            px = x0 + (i % 2) * col_w
            py = yy + (i // 2) * 16
            self._text(k, px, py, ACCENT, self.f_key)
            self._text(v, px + 66, py, TXT_MUTED, self.f_small)

        if self.context_menu.active:
            self._render_context_menu()

        if self.export_dialog.active:
            self._render_export_dialog()

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    def _render_toolbar(self):
        n = len(TOOL_ICONS)
        total_w = n * ICON_BTN + (n - 1) * ICON_GAP
        self._fill(TOOLBAR_X - 4, TOOLBAR_Y - 4, total_w + 8, ICON_BTN + 8,
                   UI_TOOLBAR, UI_TOOLBAR_BD)

        for i, (tool, label, key) in enumerate(TOOL_ICONS):
            x = TOOLBAR_X + i * (ICON_BTN + ICON_GAP)
            y = TOOLBAR_Y
            hover = (self.hovered_tool == tool)
            active = (self.tool == tool)

            if active:
                bg = (0.28, 0.50, 0.78, 1.0)
                border = bg
                ic = TXT_WHITE
            elif hover:
                bg = (0.35, 0.35, 0.35, 1.0)
                border = UI_BORDER
                ic = TXT_WHITE
            else:
                bg = (0.20, 0.20, 0.20, 1.0)
                border = UI_BORDER
                ic = TXT_MAIN

            self._fill(x, y, ICON_BTN, ICON_BTN, bg, border)
            draw_icon(tool, x, y, ICON_BTN, ic)

        if self.hovered_tool is not None:
            for tool, label, key in TOOL_ICONS:
                if tool == self.hovered_tool:
                    rect = self._toolbar_rect(tool)
                    if rect is not None:
                        tx, ty, tw_, th_ = rect
                        text = f"{label}  ({key})"
                        ui_tooltip(tx, ty + ICON_BTN + 6, text,
                                   self.height, self.f_small)
                    break

    def _render_context_menu(self):
        menu = self.context_menu
        x, y, w, h = menu.rect()

        self._fill(x, y, w, h, UI_MENU, UI_MENU_BD, 1.5)

        for i, (kind, label) in enumerate(menu.items):
            ix, iy, iw, ih = menu.item_rect(i)
            hover = (self.hovered_menu_item == i)
            if hover:
                self._fill(ix + 1, iy + 1, iw - 2, ih - 2, UI_MENU_HOVER)
            color = TXT_WHITE if hover else TXT_MAIN
            self._text(label, ix + 14, iy + (ih - self.f_body.get_height()) // 2 + 1,
                       color, self.f_body)
            kind_col = {
                "box": CUBE_COLOR,
                "sphere": (0.60, 0.66, 0.74),
                "cylinder": (0.58, 0.63, 0.71),
                "cone": (0.62, 0.62, 0.68),
                "wedge": (0.56, 0.62, 0.70),
                "kill": KILL_RED,
            }.get(kind, CUBE_COLOR)
            self._fill(ix + iw - 18, iy + (ih - 10) // 2, 8, 10, kind_col, UI_BORDER)

    def _render_export_dialog(self):
        self._fill(0, 0, self.width, self.height, (0.0, 0.0, 0.0, 0.55))

        rects = self._dialog_rects()
        px, py, panel_w, panel_h = rects["panel"]

        self._fill(px, py, panel_w, panel_h, (0.16, 0.16, 0.16, 1.0),
                   (0.30, 0.30, 0.30, 1.0), 1.5)
        self._fill(px, py, panel_w, 34, (0.11, 0.11, 0.11, 1.0))
        self._text("Export Level", px + 16, py + 8, TXT_MAIN, self.f_big)

        dialog = self.export_dialog

        lx, ly, lw, lh = rects["level"]
        self._text("Level Name", px + 20, py + 58, TXT_DIM, self.f_small)
        level_active = dialog.field == "level"
        border_col = (0.96, 0.55, 0.16, 1.0) if level_active else UI_BORDER
        self._fill(lx, ly, lw, lh, (0.10, 0.10, 0.10, 1.0), border_col, 1.5)
        lvl_txt = dialog.level_name + ("_" if level_active else "")
        self._text(lvl_txt if lvl_txt else " ", lx + 10, ly + 8, TXT_MAIN, self.f_dlg)

        ax, ay, aw, ah = rects["author"]
        self._text("Author", px + 20, py + 118, TXT_DIM, self.f_small)
        author_active = dialog.field == "author"
        border_col = (0.96, 0.55, 0.16, 1.0) if author_active else UI_BORDER
        self._fill(ax, ay, aw, ah, (0.10, 0.10, 0.10, 1.0), border_col, 1.5)
        auth_txt = dialog.author + ("_" if author_active else "")
        self._text(auth_txt if auth_txt else " ", ax + 10, ay + 8, TXT_MAIN, self.f_dlg)

        if dialog.message:
            self._text(dialog.message, px + 20, py + 184,
                       dialog.message_color, self.f_small)

        cx, cy, cw, ch = rects["cancel"]
        hover_cancel = ui_hit(cx, cy, cw, ch, self.mouse_x, self.mouse_y)
        bg_cancel = (0.24, 0.24, 0.24, 1.0) if hover_cancel else (0.20, 0.20, 0.20, 1.0)
        self._fill(cx, cy, cw, ch, bg_cancel, UI_BORDER)
        self._text("Cancel",
                   cx + (cw - text_width("Cancel", TXT_MAIN, self.f_btn)) // 2,
                   cy + 8, TXT_MAIN, self.f_btn)

        ex, ey, ew, eh = rects["export"]
        hover_export = ui_hit(ex, ey, ew, eh, self.mouse_x, self.mouse_y)
        bg_export = (0.32, 0.62, 0.90, 1.0) if hover_export else (0.28, 0.50, 0.78, 1.0)
        self._fill(ex, ey, ew, eh, bg_export, bg_export)
        self._text("Export",
                   ex + (ew - text_width("Export", TXT_WHITE, self.f_btn)) // 2,
                   ey + 8, TXT_WHITE, self.f_btn)

    def run(self):
        while self.running:
            self.clock.tick(TARGET_FPS)

            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = False
                elif ev.type == pygame.VIDEORESIZE:
                    self.width, self.height = ev.size
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height),
                        DOUBLEBUF | OPENGL | pygame.RESIZABLE,
                    )
                elif ev.type == KEYDOWN:
                    self._on_key_down(ev)
                elif ev.type == pygame.TEXTINPUT:
                    self._on_text_input(ev)
                elif ev.type == MOUSEBUTTONDOWN:
                    self._on_mouse_down(ev)
                elif ev.type == MOUSEBUTTONUP:
                    self._on_mouse_up(ev)
                elif ev.type == MOUSEMOTION:
                    self._on_mouse_motion(ev)

            self.render_3d()
            self.render_ui()
            pygame.display.flip()

        pygame.quit()
        sys.exit()
