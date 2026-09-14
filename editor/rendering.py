import math

from OpenGL.GL import (
    GL_COMPILE,
    GL_CULL_FACE,
    GL_DEPTH_TEST,
    GL_FILL,
    GL_FRONT_AND_BACK,
    GL_LINE,
    GL_LINE_LOOP,
    GL_LINES,
    GL_QUADS,
    GL_QUAD_STRIP,
    GL_TRIANGLE_FAN,
    glBegin,
    glCallList,
    glColor3f,
    glColor4f,
    glDepthMask,
    glDisable,
    glEnable,
    glEnd,
    glEndList,
    glGenLists,
    glLineWidth,
    glNewList,
    glPolygonMode,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTranslatef,
    glVertex3f,
    glVertex3fv,
)

from editor.constants import (
    CYL_EDGE,
    CYL_FILL,
    CYL_RING,
    CYL_SEGMENTS,
    FLOOR_DISC,
    GRID_BORDER,
    GRID_MAJOR,
    GRID_MINOR,
    KILL_GLOW,
    LIGHT_DIR,
)
from editor.level import Level
from editor.meshes import faces_for


_LN = math.sqrt(sum(c * c for c in LIGHT_DIR))
_LIGHT = (LIGHT_DIR[0] / _LN, LIGHT_DIR[1] / _LN, LIGHT_DIR[2] / _LN)

MOTION_COLOR = (0.35, 0.78, 1.00)
ENDPOINT_COLOR = (0.95, 0.95, 0.40)


def _normal(a, b, c):
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (
        e1[1] * e2[2] - e1[2] * e2[1],
        e1[2] * e2[0] - e1[0] * e2[2],
        e1[0] * e2[1] - e1[1] * e2[0],
    )


def _shade(n, base):
    nl = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) or 1.0
    d = abs((n[0] * _LIGHT[0] + n[1] * _LIGHT[1] + n[2] * _LIGHT[2]) / nl)
    s = 0.55 + 0.45 * d
    return (base[0] * s, base[1] * s, base[2] * s)


def _visual_position(obj):
    if obj.motion is not None and obj.motion.enabled:
        return obj.motion.effective_position(obj.position)
    return obj.position


def draw_object(obj, wireframe=False, alpha=1.0):
    pos = _visual_position(obj)
    faces = faces_for(obj.kind, obj.scale)

    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(obj.rotation[0], 1, 0, 0)
    glRotatef(obj.rotation[1], 0, 1, 0)
    glRotatef(obj.rotation[2], 0, 0, 1)

    if wireframe:
        glLineWidth(2.0)
        glColor4f(obj.color[0], obj.color[1], obj.color[2], alpha)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        for f in faces:
            if len(f) == 4:
                glBegin(GL_QUADS)
                for v in f:
                    glVertex3fv(v)
                glEnd()
            else:
                glBegin(GL_LINE_LOOP)
                for v in f:
                    glVertex3fv(v)
                glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glBegin(GL_QUADS)
        for f in faces:
            n = _normal(f[0], f[1], f[2])
            c = _shade(n, obj.color)
            glColor4f(c[0], c[1], c[2], alpha)
            for v in f:
                glVertex3fv(v)
        glEnd()

        glLineWidth(1.0)
        glColor4f(0.0, 0.0, 0.0, 0.35 * alpha)
        for f in faces:
            glBegin(GL_LINE_LOOP)
            for v in f:
                glVertex3fv(v)
            glEnd()

    glPopMatrix()


def draw_box(position, scale, rotation, color, wireframe=False, alpha=1.0):
    faces = faces_for("box", scale)
    glPushMatrix()
    glTranslatef(position[0], position[1], position[2])
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    if wireframe:
        glLineWidth(1.6)
        glColor4f(color[0], color[1], color[2], alpha)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        for f in faces:
            glBegin(GL_QUADS)
            for v in f:
                glVertex3fv(v)
            glEnd()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glBegin(GL_QUADS)
        for f in faces:
            c = _shade(_normal(f[0], f[1], f[2]), color)
            glColor4f(c[0], c[1], c[2], alpha)
            for v in f:
                glVertex3fv(v)
        glEnd()
    glPopMatrix()


def draw_motion_path(obj, endpoint_hover=False):
    m = obj.motion
    if m is None or not m.enabled:
        return
    dist = m.total_distance()
    if dist < 0.001:
        return

    start = obj.position
    end = m.endpoint(obj.position)

    glDisable(GL_DEPTH_TEST)

    glLineWidth(2.0)
    glColor4f(MOTION_COLOR[0], MOTION_COLOR[1], MOTION_COLOR[2], 0.85)
    glBegin(GL_LINES)
    glVertex3f(start[0], start[1], start[2])
    glVertex3f(end[0], end[1], end[2])
    glEnd()

    marker = 1.4
    glLineWidth(1.8)
    glColor4f(MOTION_COLOR[0], MOTION_COLOR[1], MOTION_COLOR[2], 1.0)
    glBegin(GL_LINES)
    glVertex3f(start[0] - marker, start[1], start[2])
    glVertex3f(start[0] + marker, start[1], start[2])
    glVertex3f(start[0], start[1] - marker, start[2])
    glVertex3f(start[0], start[1] + marker, start[2])
    glVertex3f(start[0], start[1], start[2] - marker)
    glVertex3f(start[0], start[1], start[2] + marker)
    glEnd()

    draw_box(end, obj.scale, obj.rotation, MOTION_COLOR, wireframe=True, alpha=0.55)

    box_size = 3.5 if endpoint_hover else 2.6
    col = ENDPOINT_COLOR if endpoint_hover else MOTION_COLOR
    draw_box(end, [box_size, box_size, box_size], [0.0, 0.0, 0.0], col)

    glEnable(GL_DEPTH_TEST)


def build_floor_list():
    lst = glGenLists(1)
    glNewList(lst, GL_COMPILE)

    r = Level.RADIUS
    n = CYL_SEGMENTS

    glColor3f(*FLOOR_DISC)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(n + 1):
        a = i / n * math.tau
        glVertex3f(math.cos(a) * r, 0.0, math.sin(a) * r)
    glEnd()

    glColor3f(*GRID_MINOR)
    glLineWidth(1.0)
    for rr in (r * 0.25, r * 0.5, r * 0.75):
        glBegin(GL_LINE_LOOP)
        for i in range(n):
            a = i / n * math.tau
            glVertex3f(math.cos(a) * rr, 0.008, math.sin(a) * rr)
        glEnd()

    glColor3f(*GRID_MAJOR)
    for i in range(Level.PARTS_PER_LAYER):
        a = i / Level.PARTS_PER_LAYER * math.tau
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.012, 0.0)
        glVertex3f(math.cos(a) * r, 0.012, math.sin(a) * r)
        glEnd()

    glColor3f(*GRID_BORDER)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    for i in range(n):
        a = i / n * math.tau
        glVertex3f(math.cos(a) * r, 0.016, math.sin(a) * r)
    glEnd()

    glEndList()
    return lst


def draw_cylinder_boundary(radius, height):
    n = CYL_SEGMENTS

    glDepthMask(False)
    glDisable(GL_CULL_FACE)
    glColor4f(*CYL_FILL)
    glBegin(GL_QUAD_STRIP)
    for i in range(n + 1):
        a = i / n * math.tau
        x, z = math.cos(a) * radius, math.sin(a) * radius
        glVertex3f(x, 0.0, z)
        glVertex3f(x, height, z)
    glEnd()
    glDepthMask(True)

    glDisable(GL_DEPTH_TEST)
    glColor4f(*CYL_RING)
    glLineWidth(1.8)
    glBegin(GL_LINE_LOOP)
    for i in range(n):
        a = i / n * math.tau
        glVertex3f(math.cos(a) * radius, 0.02, math.sin(a) * radius)
    glEnd()
    glBegin(GL_LINE_LOOP)
    for i in range(n):
        a = i / n * math.tau
        glVertex3f(math.cos(a) * radius, height, math.sin(a) * radius)
    glEnd()

    glColor4f(*CYL_EDGE)
    glLineWidth(1.0)
    for i in range(Level.PARTS_PER_LAYER):
        a = i / Level.PARTS_PER_LAYER * math.tau
        x, z = math.cos(a) * radius, math.sin(a) * radius
        glBegin(GL_LINES)
        glVertex3f(x, 0.02, z)
        glVertex3f(x, height, z)
        glEnd()
    glEnable(GL_DEPTH_TEST)


def draw_ground_shadow(obj):
    pos = _visual_position(obj)
    x = pos[0]
    z = pos[2]
    rx = obj.scale[0] * 0.55
    rz = obj.scale[2] * 0.55

    glDisable(GL_DEPTH_TEST)
    glColor4f(0.0, 0.0, 0.0, 0.28)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(x, 0.005, z)
    for i in range(24):
        a = i / 24 * math.tau
        glVertex3f(x + math.cos(a) * rx, 0.005, z + math.sin(a) * rz)
    glEnd()
    glEnable(GL_DEPTH_TEST)


def draw_kill_outline(obj):
    pos = _visual_position(obj)
    glDisable(GL_DEPTH_TEST)
    glLineWidth(2.0)
    glColor4f(*KILL_GLOW)
    y = pos[1] + obj.scale[1] * 0.5 + 0.03
    hx = obj.scale[0] * 0.5 + 0.8
    hz = obj.scale[2] * 0.5 + 0.8
    cx, cz = pos[0], pos[2]
    glBegin(GL_LINE_LOOP)
    glVertex3f(cx - hx, y, cz - hz)
    glVertex3f(cx + hx, y, cz - hz)
    glVertex3f(cx + hx, y, cz + hz)
    glVertex3f(cx - hx, y, cz + hz)
    glEnd()
    glEnable(GL_DEPTH_TEST)


def call_floor_list(lst):
    glCallList(lst)
