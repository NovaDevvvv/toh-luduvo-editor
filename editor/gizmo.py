import math

from OpenGL.GL import (
    GL_DEPTH_TEST,
    GL_LINE_LOOP,
    GL_LINES,
    glBegin,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glLineWidth,
    glVertex3f,
)

from editor.constants import (
    AXIS_ACTIVE,
    AXIS_COLORS,
    AXIS_HOVER,
    AXIS_VECTORS,
    GIZMO_LENGTH,
    GIZMO_PICK_PX,
    RING_SEGMENTS,
)
from editor.projection import project, seg_dist_2d
from editor.rendering import draw_box


def draw_gizmo(obj, mode, hovered, active):
    ox, oy, oz = obj.position
    length = GIZMO_LENGTH

    glDisable(GL_DEPTH_TEST)

    def col(i):
        if active == i:
            return AXIS_ACTIVE
        if hovered == i:
            return AXIS_HOVER
        return AXIS_COLORS[i]

    if mode in ("move", "scale"):
        glLineWidth(3.5)
        for i in range(3):
            glColor3f(*col(i))
            glBegin(GL_LINES)
            glVertex3f(ox, oy, oz)
            glVertex3f(
                ox + AXIS_VECTORS[i][0] * length,
                oy + AXIS_VECTORS[i][1] * length,
                oz + AXIS_VECTORS[i][2] * length,
            )
            glEnd()

        for i in range(3):
            tip = (
                ox + AXIS_VECTORS[i][0] * length,
                oy + AXIS_VECTORS[i][1] * length,
                oz + AXIS_VECTORS[i][2] * length,
            )
            size = 2.2 if mode == "move" else 3.0
            draw_box(tip, [size, size, size], [0.0, 0.0, 0.0], col(i))

    elif mode == "rotate":
        radius = GIZMO_LENGTH * 0.95
        segs = RING_SEGMENTS
        for i in range(3):
            glColor3f(*col(i))
            glLineWidth(3.0)
            glBegin(GL_LINE_LOOP)
            for s in range(segs):
                t = s / segs * math.tau
                if i == 0:
                    glVertex3f(ox, oy + math.cos(t) * radius, oz + math.sin(t) * radius)
                elif i == 1:
                    glVertex3f(ox + math.cos(t) * radius, oy, oz + math.sin(t) * radius)
                else:
                    glVertex3f(ox + math.cos(t) * radius, oy + math.sin(t) * radius, oz)
            glEnd()

    glEnable(GL_DEPTH_TEST)


def pick_gizmo_axis(obj, tool, mx, my, cam, vw, vh):
    if obj is None:
        return None

    center = project(obj.position, cam, vw, vh)
    if center is None:
        return None

    best = None
    best_d = GIZMO_PICK_PX

    if tool in ("move", "scale"):
        ox, oy, oz = obj.position
        for i in range(3):
            av = AXIS_VECTORS[i]
            tip = project(
                (ox + av[0] * GIZMO_LENGTH,
                 oy + av[1] * GIZMO_LENGTH,
                 oz + av[2] * GIZMO_LENGTH),
                cam, vw, vh,
            )
            if tip is None:
                continue
            d = seg_dist_2d(mx, my, center[0], center[1], tip[0], tip[1])
            if d < best_d:
                best_d = d
                best = i

    elif tool == "rotate":
        radius = GIZMO_LENGTH * 0.95
        segs = 40
        ox, oy, oz = obj.position
        for i in range(3):
            prev = None
            for s in range(segs + 1):
                t = s / segs * math.tau
                if i == 0:
                    p = (ox, oy + math.cos(t) * radius, oz + math.sin(t) * radius)
                elif i == 1:
                    p = (ox + math.cos(t) * radius, oy, oz + math.sin(t) * radius)
                else:
                    p = (ox + math.cos(t) * radius, oy + math.sin(t) * radius, oz)
                sp = project(p, cam, vw, vh)
                if sp is None:
                    prev = None
                    continue
                if prev is not None:
                    d = seg_dist_2d(mx, my, prev[0], prev[1], sp[0], sp[1])
                    if d < best_d:
                        best_d = d
                        best = i
                prev = sp

    return best
