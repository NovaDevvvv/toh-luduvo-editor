import math

from editor.constants import (
    END_COLOR,
    SHAPE_COLOR,
    SHAPE_DEFAULTS,
    SHAPE_PREFIX,
    START_COLOR,
)
from editor.math3d import clamp
from editor.objects import Object3D


class Level:
    RADIUS = 70.0
    WALL_THICKNESS = 2.0
    INNER_RADIUS = RADIUS - WALL_THICKNESS / 2.0
    LEDGE_DEPTH = 11.0
    LEDGE_RADIUS = INNER_RADIUS - LEDGE_DEPTH / 2.0
    PARTS_PER_LAYER = 16
    SEGMENT_WIDTH = 2.0 * RADIUS * math.sin(math.pi / PARTS_PER_LAYER) * 1.15

    HEIGHT_MIN = 10.0
    HEIGHT_MAX = 200.0
    HEIGHT_STEP = 1.0

    MAX_OBJECT_RADIUS = INNER_RADIUS - 2.0

    def __init__(self):
        self.height = 40.0
        self.start_angle = 0.0
        self.end_angle = math.pi
        self.start_pad = None
        self.end_pad = None
        self.objects = []
        self._rebuild_pads()

    def _make_pad(self, name, angle, y, color, kind):
        return Object3D(
            name=name,
            position=[
                math.cos(angle) * Level.LEDGE_RADIUS,
                y,
                math.sin(angle) * Level.LEDGE_RADIUS,
            ],
            scale=[Level.LEDGE_DEPTH, 1.0, Level.SEGMENT_WIDTH * 1.4],
            rotation=[0.0, -math.degrees(angle), 0.0],
            color=color,
            kind=kind,
            locked=True,
        )

    def _rebuild_pads(self):
        self.start_pad = self._make_pad(
            "Start Pad", self.start_angle, 0.5, START_COLOR, "start"
        )
        self.end_pad = self._make_pad(
            "End Pad", self.end_angle, self.height - 0.5, END_COLOR, "end"
        )

    def set_height(self, h):
        self.height = clamp(h, self.HEIGHT_MIN, self.HEIGHT_MAX)
        if self.end_pad is not None:
            self.end_pad.position[1] = self.height - 0.5
        for obj in self.objects:
            self.clamp_position(obj)

    def reset(self):
        self.objects = []
        self._rebuild_pads()

    def _next_name(self, prefix):
        existing = {o.name for o in self.objects}
        n = 1
        while f"{prefix}_{n}" in existing:
            n += 1
        return f"{prefix}_{n}"

    def add_shape(self, kind, position=None):
        if position is None:
            position = [0.0, None, 0.0]
        scale = list(SHAPE_DEFAULTS.get(kind, SHAPE_DEFAULTS["box"]))
        color = SHAPE_COLOR.get(kind, SHAPE_COLOR["box"])
        prefix = SHAPE_PREFIX.get(kind, "Part")

        y = position[1] if position[1] is not None else scale[1] * 0.5

        obj = Object3D(
            name=self._next_name(prefix),
            position=[position[0], y, position[2]],
            scale=scale,
            rotation=[0.0, 0.0, 0.0],
            color=color,
            kind=kind,
        )
        self.clamp_position(obj)
        self.objects.append(obj)
        return obj

    def horizontal_extent(self, obj):
        return max(obj.scale[0], obj.scale[2]) * 0.5

    def clamp_position(self, obj):
        if obj.locked:
            return
        half_y = obj.scale[1] * 0.5
        lo = half_y
        hi = self.height - half_y
        if hi < lo:
            hi = lo
        obj.position[1] = clamp(obj.position[1], lo, hi)

        r = math.hypot(obj.position[0], obj.position[2])
        ext = self.horizontal_extent(obj)
        lim = Level.MAX_OBJECT_RADIUS - ext
        if lim < 0.5:
            lim = 0.5
        if r > lim and r > 1e-6:
            s = lim / r
            obj.position[0] *= s
            obj.position[2] *= s

    def clamp_new_position(self, x, z):
        r = math.hypot(x, z)
        lim = Level.MAX_OBJECT_RADIUS
        if r > lim and r > 1e-6:
            s = lim / r
            return x * s, z * s
        return x, z
