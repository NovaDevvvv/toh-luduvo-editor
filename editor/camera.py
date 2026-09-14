import math

from editor.math3d import clamp, v_cross, v_norm, v_sub


class Camera:
    __slots__ = ("target", "distance", "yaw", "pitch", "fov", "near", "far")

    def __init__(self):
        self.target = [0.0, 20.0, 0.0]
        self.distance = 240.0
        self.yaw = math.radians(35.0)
        self.pitch = math.radians(-25.0)
        self.fov = 45.0
        self.near = 0.5
        self.far = 4000.0

    def position(self):
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        d = self.distance
        return [
            self.target[0] + d * cp * sy,
            self.target[1] + d * sp,
            self.target[2] + d * cp * cy,
        ]

    def forward(self):
        return v_norm(v_sub(self.target, self.position()))

    def right(self):
        return v_norm(v_cross(self.forward(), (0.0, 1.0, 0.0)))

    def up(self):
        return v_cross(self.right(), self.forward())

    def orbit(self, dx, dy):
        self.yaw -= dx * 0.005
        self.pitch += dy * 0.005
        self.pitch = clamp(self.pitch, math.radians(-88), math.radians(88))

    def pan(self, dx, dy):
        r = self.right()
        u = self.up()
        t = self.target
        t[0] += (-r[0] * dx + u[0] * dy) * 0.12
        t[1] += (-r[1] * dx + u[1] * dy) * 0.12
        t[2] += (-r[2] * dx + u[2] * dy) * 0.12

    def zoom(self, amount):
        self.distance = clamp(self.distance + amount, 20.0, 1500.0)

    def set_view(self, name):
        if name == "front":
            self.yaw, self.pitch = 0.0, 0.0
        elif name == "right":
            self.yaw, self.pitch = math.radians(90.0), 0.0
        elif name == "top":
            self.yaw, self.pitch = 0.0, math.radians(88.0)
        elif name == "persp":
            self.yaw, self.pitch = math.radians(35.0), math.radians(-25.0)
