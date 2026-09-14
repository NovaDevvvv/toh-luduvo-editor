from dataclasses import dataclass


@dataclass
class Motion:
    enabled: bool = False
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0
    speed: float = 5.0
    phase: float = 0.0

    def total_distance(self):
        return (self.dx * self.dx + self.dy * self.dy + self.dz * self.dz) ** 0.5

    def offset(self):
        if not self.enabled:
            return (0.0, 0.0, 0.0)
        dist = self.total_distance()
        if dist < 1e-6:
            return (0.0, 0.0, 0.0)
        p = self.phase % 1.0
        u = p * 2.0 if p < 0.5 else 2.0 - p * 2.0
        return (self.dx * u, self.dy * u, self.dz * u)

    def effective_position(self, base):
        ox, oy, oz = self.offset()
        return [base[0] + ox, base[1] + oy, base[2] + oz]

    def endpoint(self, base):
        return [base[0] + self.dx, base[1] + self.dy, base[2] + self.dz]

    def tick(self, dt):
        if not self.enabled:
            return
        dist = self.total_distance()
        if dist < 1e-6:
            return
        rate = self.speed / (2.0 * dist)
        self.phase = (self.phase + rate * dt) % 1.0

    def to_dict(self):
        if not self.enabled and self.dx == 0.0 and self.dy == 0.0 and self.dz == 0.0:
            return None
        d = {"enabled": bool(self.enabled)}
        if self.dx: d["dx"] = self.dx
        if self.dy: d["dy"] = self.dy
        if self.dz: d["dz"] = self.dz
        if self.speed != 5.0: d["speed"] = self.speed
        return d

    @staticmethod
    def from_dict(d):
        if not d:
            return Motion()
        return Motion(
            enabled=bool(d.get("enabled", False)),
            dx=float(d.get("dx", d.get("distance", 0.0))) if d.get("axis", "x") == "x" else 0.0,
            dy=float(d.get("dy", d.get("distance", 0.0))) if d.get("axis", "x") == "y" else 0.0,
            dz=float(d.get("dz", d.get("distance", 0.0))) if d.get("axis", "x") == "z" else 0.0,
            speed=float(d.get("speed", 5.0)),
            phase=float(d.get("phase", 0.0)),
        )

    @staticmethod
    def from_dict_v2(d):
        if not d:
            return Motion()
        return Motion(
            enabled=bool(d.get("enabled", False)),
            dx=float(d.get("dx", 0.0)),
            dy=float(d.get("dy", 0.0)),
            dz=float(d.get("dz", 0.0)),
            speed=float(d.get("speed", 5.0)),
        )


@dataclass
class Object3D:
    name: str
    position: list
    scale: list
    rotation: list
    color: tuple
    kind: str = "box"
    locked: bool = False
    motion: Motion = None

    def __post_init__(self):
        if self.motion is None:
            self.motion = Motion()

    def to_dict(self):
        md = self.motion.to_dict()
        d = {
            "n": self.name,
            "p": self.position,
            "s": self.scale,
            "r": self.rotation,
            "c": _color_hex(self.color),
        }
        if self.kind != "box":
            d["k"] = self.kind
        if md is not None:
            d["m"] = md
        return d

    def clone(self, new_name=None):
        return Object3D(
            name=new_name or self.name,
            position=list(self.position),
            scale=list(self.scale),
            rotation=list(self.rotation),
            color=tuple(self.color),
            kind=self.kind,
            locked=False,
            motion=Motion(**vars(self.motion)),
        )

    @staticmethod
    def from_dict(d):
        if "position" in d:
            return Object3D(
                name=d["name"],
                position=list(d["position"]),
                scale=list(d["scale"]),
                rotation=list(d["rotation"]),
                color=tuple(d["color"]),
                kind=d.get("kind", "box"),
                locked=d.get("locked", False),
                motion=Motion.from_dict_v2(d.get("motion")),
            )
        return Object3D(
            name=d.get("n", "Object"),
            position=list(d.get("p", [0.0, 0.0, 0.0])),
            scale=list(d.get("s", [1.0, 1.0, 1.0])),
            rotation=list(d.get("r", [0.0, 0.0, 0.0])),
            color=_hex_color(d.get("c", "#8f9bb0")),
            kind=d.get("k", "box"),
            locked=False,
            motion=Motion.from_dict_v2(d.get("m")),
        )


def _color_hex(c):
    r = max(0, min(255, int(round(c[0] * 255))))
    g = max(0, min(255, int(round(c[1] * 255))))
    b = max(0, min(255, int(round(c[2] * 255))))
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def _hex_color(s):
    s = s.lstrip("#")
    if len(s) != 6:
        return (0.56, 0.61, 0.68)
    return (
        int(s[0:2], 16) / 255.0,
        int(s[2:4], 16) / 255.0,
        int(s[4:6], 16) / 255.0,
    )
