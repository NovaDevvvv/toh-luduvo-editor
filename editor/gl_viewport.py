import math
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QMenu

from OpenGL.GL import (
    GL_BACK,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINE_LOOP,
    GL_LINES,
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
    glShadeModel,
    glVertex3f,
    glViewport,
)
from OpenGL.GLU import gluLookAt, gluPerspective

from editor.camera import Camera
from editor.constants import (
    AXIS_VECTORS,
    END_PILLAR,
    GL_BG,
    KILL_SHAPE,
    SELECTION_COLOR,
    SHAPES,
    SHAPE_PREFIX,
    START_PILLAR,
)
from editor.gizmo import draw_gizmo, pick_gizmo_axis
from editor.history import History
from editor.icons import kill_icon
from editor.level import Level
from editor.objects import Motion
from editor.projection import (
    closest_t_on_axis,
    project,
    ray_intersect_plane,
    ray_intersect_plane_y,
    screen_to_ray,
)
from editor.rendering import (
    build_floor_list,
    call_floor_list,
    draw_box,
    draw_cylinder_boundary,
    draw_ground_shadow,
    draw_kill_outline,
    draw_motion_path,
    draw_object,
)


TOOL_MOVE = "move"
TOOL_SCALE = "scale"
TOOL_ROTATE = "rotate"
TOOL_SELECT = "select"

ENDPOINT_PICK_PX = 14.0


class GLViewport(QOpenGLWidget):
    selectionChanged = Signal(object)
    levelChanged = Signal(object)
    toolChanged = Signal(str)
    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(480, 360)

        self.level = Level()
        self.camera = Camera()
        self.history = History()

        self.selected_index = None
        self.tool = TOOL_MOVE
        self.axis = "xyz"
        self.clipboard = None

        self.hovered_axis = None
        self.hovered_endpoint = False
        self.active_axis = None
        self.drag_mode = None
        self.drag_last = None
        self.drag_origin = None
        self.drag_moved = False
        self.drag_button = None

        self.drag_start_pos = None
        self.drag_start_rot = None
        self.drag_start_scl = None
        self.drag_start_t = 0.0
        self.drag_start_mx = 0

        self.endpoint_drag_start = None
        self.endpoint_drag_plane_p = None
        self.endpoint_drag_plane_n = None
        self.endpoint_drag_world0 = None

        self.motion_copy_source = None

        self._floor_list = None

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._last_tick = time.time()

        self.history.push(self.level)
        self._anim_timer.start()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glClearColor(*GL_BG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glShadeModel(GL_SMOOTH)

        self._floor_list = build_floor_list()

    def resizeGL(self, w, h):
        glViewport(0, 0, max(1, w), max(1, h))

    def _tick_animation(self):
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        if dt > 0.1:
            dt = 0.1
        if dt <= 0.0:
            return

        sel = self.get_selected()
        dirty = False
        for obj in self.level.objects:
            if obj.motion is not None and obj.motion.enabled and obj is not sel:
                obj.motion.tick(dt)
                dirty = True

        if dirty:
            self.update()

    def _visual_position(self, obj):
        if obj.motion is not None and obj.motion.enabled:
            return obj.motion.effective_position(obj.position)
        return obj.position

    def _endpoint_screen(self, obj):
        if obj.motion is None or not obj.motion.enabled:
            return None
        end = obj.motion.endpoint(obj.position)
        return project(end, self.camera, self.width(), self.height())

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = max(1, self.width())
        h = max(1, self.height())

        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.fov, w / h, self.camera.near, self.camera.far)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        p = self.camera.position()
        t = self.camera.target
        gluLookAt(p[0], p[1], p[2], t[0], t[1], t[2], 0.0, 1.0, 0.0)

        call_floor_list(self._floor_list)
        draw_cylinder_boundary(Level.RADIUS, self.level.height)

        for obj in self.level.objects:
            draw_ground_shadow(obj)

        for obj in self.level.objects:
            draw_object(obj)
            if obj.kind == "kill":
                draw_kill_outline(obj)

        self._draw_pads()

        sel = self.get_selected()
        if sel is not None and not sel.locked:
            if sel.motion is not None and sel.motion.enabled:
                draw_motion_path(sel, endpoint_hover=self.hovered_endpoint)

            glDisable(GL_DEPTH_TEST)
            visual = self._visual_position(sel)
            draw_box(
                visual,
                [sel.scale[0] + 0.6, sel.scale[1] + 0.6, sel.scale[2] + 0.6],
                sel.rotation,
                SELECTION_COLOR,
                wireframe=True,
            )
            glEnable(GL_DEPTH_TEST)

            if self.tool != TOOL_SELECT and not self.hovered_endpoint:
                draw_gizmo(sel, self.tool, self.hovered_axis, self.active_axis)

    def _draw_pads(self):
        for pad, pillar in (
            (self.level.start_pad, START_PILLAR),
            (self.level.end_pad, END_PILLAR),
        ):
            draw_box(
                pad.position,
                [pad.scale[0] * 0.9, 0.4, pad.scale[2] * 0.9],
                pad.rotation,
                pad.color,
            )

            x = pad.position[0]
            y = pad.position[1]
            z = pad.position[2]
            sx = pad.scale[0] * 0.5
            sz = pad.scale[2] * 0.5
            yaw = math.radians(pad.rotation[1])
            c, s = math.cos(yaw), math.sin(yaw)

            corners = []
            for dx, dz in ((-sx, -sz), (sx, -sz), (sx, sz), (-sx, sz)):
                rx = dx * c - dz * s
                rz = dx * s + dz * c
                corners.append((x + rx, z + rz))

            glDisable(GL_DEPTH_TEST)
            glLineWidth(2.0)
            glColor4f(*pillar)
            glBegin(GL_LINE_LOOP)
            for cx, cz in corners:
                glVertex3f(cx, y + 0.25, cz)
            glEnd()
            glBegin(GL_LINE_LOOP)
            for cx, cz in corners:
                glVertex3f(cx, y + 6.0, cz)
            glEnd()
            glBegin(GL_LINES)
            for cx, cz in corners:
                glVertex3f(cx, y + 0.25, cz)
                glVertex3f(cx, y + 6.0, cz)
            glEnd()
            glEnable(GL_DEPTH_TEST)

    def get_selected(self):
        if self.selected_index is None:
            return None
        if 0 <= self.selected_index < len(self.level.objects):
            return self.level.objects[self.selected_index]
        return None

    def set_tool(self, tool):
        if tool != self.tool:
            self.tool = tool
            self.toolChanged.emit(tool)
            self.update()

    def set_axis(self, axis):
        self.axis = axis

    def pick_object(self, mx, my):
        best = None
        best_d = 55.0
        for i, obj in enumerate(self.level.objects):
            visual = self._visual_position(obj)
            p = project(visual, self.camera, self.width(), self.height())
            if p is None:
                continue
            d = math.hypot(p[0] - mx, p[1] - my)
            thr = 25.0 + max(obj.scale) * 0.4
            if thr > 90.0:
                thr = 90.0
            if d < best_d and d < thr:
                best_d = d
                best = i
        return best

    def _pick_gizmo(self, mx, my):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return None
        return pick_gizmo_axis(
            obj, self.tool, mx, my, self.camera, self.width(), self.height()
        )

    def _pick_endpoint(self, mx, my):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return False
        if obj.motion is None or not obj.motion.enabled:
            return False
        if obj.motion.total_distance() < 0.001:
            return False
        p = self._endpoint_screen(obj)
        if p is None:
            return False
        return math.hypot(p[0] - mx, p[1] - my) <= ENDPOINT_PICK_PX

    def _raycast_ground(self, mx, my):
        ro, rd = screen_to_ray(mx, my, self.camera, self.width(), self.height())
        return ray_intersect_plane_y(ro, rd, 0.0)

    def mousePressEvent(self, ev):
        self.setFocus()
        pos = ev.position().toPoint()
        self.drag_origin = pos
        self.drag_last = pos
        self.drag_moved = False
        self.drag_button = ev.button()

        mx, my = pos.x(), pos.y()

        if ev.button() == Qt.LeftButton:
            if self.motion_copy_source is not None:
                idx = self.pick_object(mx, my)
                if idx is not None:
                    target = self.level.objects[idx]
                    src = self.motion_copy_source
                    target.motion = Motion(**vars(src.motion))
                    self.motion_copy_source = None
                    self.levelChanged.emit(None)
                    self.statusMessage.emit(f"Motion copied from {src.name} to {target.name}")
                    self.update()
                    return
                self.motion_copy_source = None
                self.statusMessage.emit("Motion copy cancelled")
                self.update()
                return

            if self._pick_endpoint(mx, my):
                self._begin_endpoint_drag(mx, my)
                return

            axis = self._pick_gizmo(mx, my)
            if axis is not None:
                self._begin_axis_drag(axis, mx, my)
                return

            idx = self.pick_object(mx, my)
            if idx is not None:
                self._set_selection(idx)
                return

            self._set_selection(None)
            self.drag_mode = "orbit"

        elif ev.button() == Qt.MiddleButton:
            self.drag_mode = "pan" if (ev.modifiers() & Qt.ShiftModifier) else "orbit"

        elif ev.button() == Qt.RightButton:
            self.drag_mode = "rmb_undecided"

        ev.accept()

    def mouseMoveEvent(self, ev):
        pos = ev.position().toPoint()
        mx, my = pos.x(), pos.y()

        if self.drag_mode is None:
            self.hovered_endpoint = self._pick_endpoint(mx, my)
            if self.hovered_endpoint:
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            self.hovered_axis = None if self.hovered_endpoint else self._pick_gizmo(mx, my)
            self.update()
            return

        dx = mx - self.drag_last.x()
        dy = my - self.drag_last.y()
        self.drag_last = pos

        if (abs(mx - self.drag_origin.x()) > 3 or
                abs(my - self.drag_origin.y()) > 3):
            self.drag_moved = True

        if self.drag_mode == "orbit":
            self.camera.orbit(dx, dy)
            self.update()
        elif self.drag_mode == "pan":
            self.camera.pan(dx, dy)
            self.update()
        elif self.drag_mode == "rmb_undecided":
            if self.drag_moved:
                self.drag_mode = "pan"
                self.camera.pan(dx, dy)
                self.update()
        elif self.drag_mode == "axis":
            self._update_axis_drag(mx, my)
        elif self.drag_mode == "endpoint":
            self._update_endpoint_drag(mx, my)

    def mouseReleaseEvent(self, ev):
        if (ev.button() == Qt.RightButton
                and self.drag_mode == "rmb_undecided"
                and not self.drag_moved):
            pos = ev.position().toPoint()
            world = self._raycast_ground(pos.x(), pos.y())
            if world is None:
                t = self.camera.target
                world = (t[0], 0.0, t[2])
            self._open_context_menu(
                ev.globalPosition().toPoint(), world, pos.x(), pos.y()
            )

        self.drag_mode = None
        self.active_axis = None
        self.drag_button = None

    def wheelEvent(self, ev):
        delta = ev.angleDelta().y()
        self.camera.zoom(-delta / 120.0 * 18.0)
        self.update()

    def keyPressEvent(self, ev):
        k = ev.key()
        mods = ev.modifiers()
        ctrl = bool(mods & Qt.ControlModifier)

        if k == Qt.Key_G:
            self.set_tool(TOOL_MOVE)
        elif k == Qt.Key_S and not ctrl:
            self.set_tool(TOOL_SCALE)
        elif k == Qt.Key_R:
            self.set_tool(TOOL_ROTATE)
        elif k == Qt.Key_Q:
            self.set_tool(TOOL_SELECT)
        elif k == Qt.Key_X:
            self.set_axis("x")
        elif k == Qt.Key_Y:
            self.set_axis("y")
        elif k == Qt.Key_Z and not ctrl:
            self.set_axis("z")
        elif k == Qt.Key_0:
            self.set_axis("xyz")
        elif k == Qt.Key_1:
            self.camera.set_view("front"); self.update()
        elif k == Qt.Key_3:
            self.camera.set_view("right"); self.update()
        elif k == Qt.Key_7:
            self.camera.set_view("top"); self.update()
        elif k == Qt.Key_5:
            self.camera.set_view("persp"); self.update()
        elif k == Qt.Key_Delete:
            self.delete_selected()
        elif k == Qt.Key_Escape:
            if self.motion_copy_source is not None:
                self.motion_copy_source = None
                self.statusMessage.emit("Motion copy cancelled")
                self.update()
            else:
                ev.ignore()
                return
        else:
            ev.ignore()
            return
        ev.accept()

    def _set_selection(self, idx):
        if idx == self.selected_index:
            return
        self.selected_index = idx

        new_sel = self.get_selected()
        if new_sel is not None and new_sel.motion is not None:
            new_sel.motion.phase = 0.0

        self.selectionChanged.emit(new_sel)
        self.update()

    def _begin_axis_drag(self, axis, mx, my):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        self.history.push(self.level)
        self.drag_mode = "axis"
        self.active_axis = axis
        self.drag_start_pos = list(obj.position)
        self.drag_start_rot = list(obj.rotation)
        self.drag_start_scl = list(obj.scale)
        self.drag_start_mx = mx
        ro, rd = screen_to_ray(mx, my, self.camera, self.width(), self.height())
        self.drag_start_t = closest_t_on_axis(
            ro, rd, self.drag_start_pos, AXIS_VECTORS[axis]
        )

    def _update_axis_drag(self, mx, my):
        obj = self.get_selected()
        if obj is None or self.active_axis is None:
            return
        axis = self.active_axis
        ro, rd = screen_to_ray(mx, my, self.camera, self.width(), self.height())
        t = closest_t_on_axis(ro, rd, self.drag_start_pos, AXIS_VECTORS[axis])
        delta = t - self.drag_start_t

        if self.tool == TOOL_MOVE:
            obj.position[axis] = self.drag_start_pos[axis] + delta
            self.level.clamp_position(obj)
        elif self.tool == TOOL_SCALE:
            obj.scale[axis] = max(0.5, self.drag_start_scl[axis] + delta)
            self.level.clamp_position(obj)
        elif self.tool == TOOL_ROTATE:
            dx_px = mx - self.drag_start_mx
            obj.rotation[axis] = self.drag_start_rot[axis] + dx_px * 0.5

        self.levelChanged.emit(None)
        self.update()

    def _begin_endpoint_drag(self, mx, my):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        m = obj.motion
        if m is None or not m.enabled:
            return

        self.history.push(self.level)
        self.drag_mode = "endpoint"

        end = m.endpoint(obj.position)
        cam_pos = self.camera.position()
        fwd = (
            self.camera.target[0] - cam_pos[0],
            self.camera.target[1] - cam_pos[1],
            self.camera.target[2] - cam_pos[2],
        )
        ln = math.sqrt(fwd[0] * fwd[0] + fwd[1] * fwd[1] + fwd[2] * fwd[2]) or 1.0
        normal = (fwd[0] / ln, fwd[1] / ln, fwd[2] / ln)

        self.endpoint_drag_plane_p = list(end)
        self.endpoint_drag_plane_n = normal

        ro, rd = screen_to_ray(mx, my, self.camera, self.width(), self.height())
        hit = ray_intersect_plane(ro, rd, end, normal)
        if hit is None:
            self.drag_mode = None
            return

        self.endpoint_drag_world0 = hit
        self.endpoint_drag_start = (m.dx, m.dy, m.dz)

    def _update_endpoint_drag(self, mx, my):
        obj = self.get_selected()
        if obj is None or obj.motion is None:
            return
        if self.endpoint_drag_world0 is None:
            return

        ro, rd = screen_to_ray(mx, my, self.camera, self.width(), self.height())
        hit = ray_intersect_plane(
            ro, rd, self.endpoint_drag_plane_p, self.endpoint_drag_plane_n
        )
        if hit is None:
            return

        dx = hit[0] - self.endpoint_drag_world0[0]
        dy = hit[1] - self.endpoint_drag_world0[1]
        dz = hit[2] - self.endpoint_drag_world0[2]

        sx, sy, sz = self.endpoint_drag_start
        m = obj.motion
        m.dx = max(-500.0, min(500.0, sx + dx))
        m.dy = max(-500.0, min(500.0, sy + dy))
        m.dz = max(-500.0, min(500.0, sz + dz))

        self.levelChanged.emit(None)
        self.update()

    def _open_context_menu(self, global_pos, world_pos, mx, my):
        idx = self.pick_object(mx, my)
        menu = QMenu(self)

        if idx is not None:
            self._set_selection(idx)
            obj = self.level.objects[idx]

            motion_sub = menu.addMenu("Motion")
            enable_act = motion_sub.addAction("Enable moving")
            enable_act.setCheckable(True)
            enable_act.setChecked(obj.motion.enabled)

            motion_sub.addSeparator()
            jump_act = motion_sub.addAction("Go to first frame")
            preview_act = motion_sub.addAction("Preview half-way")
            flip_act = motion_sub.addAction("Flip direction")
            clear_act = motion_sub.addAction("Clear motion")

            copy_motion_act = menu.addAction("Copy motion to another part...")

            menu.addSeparator()
            copy_act = menu.addAction("Copy part")
            delete_act = menu.addAction("Delete")

            chosen = menu.exec(global_pos)

            if chosen is enable_act:
                obj.motion.enabled = not obj.motion.enabled
                obj.motion.phase = 0.0
                self.levelChanged.emit(None)
                self.update()
            elif chosen is jump_act:
                obj.motion.phase = 0.0
                self.levelChanged.emit(None)
                self.update()
            elif chosen is preview_act:
                obj.motion.phase = 0.5
                self.levelChanged.emit(None)
                self.update()
            elif chosen is flip_act:
                obj.motion.dx = -obj.motion.dx
                obj.motion.dy = -obj.motion.dy
                obj.motion.dz = -obj.motion.dz
                self.levelChanged.emit(None)
                self.update()
            elif chosen is clear_act:
                obj.motion = Motion()
                self.levelChanged.emit(None)
                self.update()
            elif chosen is copy_motion_act:
                self.motion_copy_source = obj
                self.statusMessage.emit(
                    f"Motion armed — click another part to paste {obj.name}'s motion"
                )
                self.update()
            elif chosen is copy_act:
                self.copy_selected()
            elif chosen is delete_act:
                self.delete_selected()
        else:
            actions = {}
            for kind, label in SHAPES:
                act = menu.addAction(label)
                actions[act] = kind

            menu.addSeparator()

            kill_kind, kill_label = KILL_SHAPE
            kill_act = menu.addAction(kill_icon(), kill_label)
            actions[kill_act] = kill_kind

            chosen = menu.exec(global_pos)
            if chosen is not None and chosen in actions:
                self._spawn_at(actions[chosen], world_pos)

    def _spawn_at(self, kind, world_pos):
        x, z = self.level.clamp_new_position(world_pos[0], world_pos[2])
        self.history.push(self.level)
        obj = self.level.add_shape(kind, [x, None, z])
        idx = self.level.objects.index(obj)
        self._set_selection(idx)
        self.levelChanged.emit(None)
        self.update()

    def add_shape_center(self, kind):
        world = self._raycast_ground(self.width() // 2, self.height() // 2)
        if world is None:
            t = self.camera.target
            world = (t[0], 0.0, t[2])
        self._spawn_at(kind, world)

    def delete_selected(self):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        self.history.push(self.level)
        del self.level.objects[self.selected_index]
        new_idx = min(self.selected_index, len(self.level.objects) - 1)
        self._set_selection(new_idx if new_idx >= 0 else None)
        self.levelChanged.emit(None)
        self.update()

    def copy_selected(self):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        self.clipboard = obj.clone()

    def paste_clipboard(self):
        if self.clipboard is None:
            return
        self.history.push(self.level)
        clone = self.clipboard.clone()
        prefix = SHAPE_PREFIX.get(clone.kind, "Part")
        clone.name = self.level._next_name(prefix)
        self.level.clamp_position(clone)
        self.level.objects.append(clone)
        self._set_selection(len(self.level.objects) - 1)
        self.levelChanged.emit(None)
        self.update()

    def undo(self):
        if self.history.undo(self.level):
            self._set_selection(None)
            self.levelChanged.emit(None)
            self.update()

    def redo(self):
        if self.history.redo(self.level):
            self._set_selection(None)
            self.levelChanged.emit(None)
            self.update()

    def set_height(self, height):
        self.history.push(self.level)
        self.level.set_height(height)
        self.levelChanged.emit(None)
        self.update()

    def reset_level(self):
        self.history.push(self.level)
        self.level.reset()
        self._set_selection(None)
        self.levelChanged.emit(None)
        self.update()

    def apply_property(self, field, axis, value):
        obj = self.get_selected()
        if obj is None or obj.locked:
            return
        arr = getattr(obj, field, None)
        if arr is None:
            return
        arr[axis] = value
        self.level.clamp_position(obj)
        self.levelChanged.emit(None)
        self.update()
