APP_NAME = "Tower Level Editor"
APP_VERSION = "2.0.0"

VIEWPORT_MIN_W = 480
VIEWPORT_MIN_H = 360
SIDEBAR_WIDTH = 320

GL_BG = (0.145, 0.145, 0.145, 1.0)

FLOOR_DISC = (0.175, 0.175, 0.175)
GRID_MINOR = (0.215, 0.215, 0.215)
GRID_MAJOR = (0.280, 0.280, 0.280)
GRID_BORDER = (0.360, 0.360, 0.360)
CYL_FILL = (0.360, 0.520, 0.750, 0.048)
CYL_RING = (0.450, 0.640, 0.930, 0.550)
CYL_EDGE = (0.400, 0.570, 0.830, 0.240)

BOX_COLOR = (0.560, 0.610, 0.680)
SPHERE_COLOR = (0.620, 0.660, 0.730)
CYLINDER_COLOR = (0.590, 0.640, 0.710)
CONE_COLOR = (0.640, 0.610, 0.680)
WEDGE_COLOR = (0.570, 0.630, 0.700)
KILL_COLOR = (0.870, 0.290, 0.320)

START_COLOR = (0.290, 0.760, 0.400)
END_COLOR = (0.320, 0.620, 0.920)
START_PILLAR = (0.290, 0.760, 0.400, 0.35)
END_PILLAR = (0.320, 0.620, 0.920, 0.35)

KILL_GLOW = (1.000, 0.340, 0.380, 0.850)
SELECTION_COLOR = (1.000, 0.650, 0.150)

AXIS_COLORS = (
    (0.920, 0.300, 0.300),
    (0.400, 0.820, 0.320),
    (0.300, 0.560, 0.950),
)
AXIS_HOVER = (1.000, 0.940, 0.380)
AXIS_ACTIVE = (1.000, 1.000, 0.400)

AXIS_VECTORS = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)

GIZMO_LENGTH = 16.0
GIZMO_PICK_PX = 12.0
RING_SEGMENTS = 64
CYL_SEGMENTS = 96

SHAPES = (
    ("box", "Box"),
    ("sphere", "Sphere"),
    ("cylinder", "Cylinder"),
    ("cone", "Cone"),
    ("wedge", "Wedge"),
)

KILL_SHAPE = ("kill", "Kill Part")

SHAPE_DEFAULTS = {
    "box": (6.0, 4.0, 6.0),
    "sphere": (6.0, 6.0, 6.0),
    "cylinder": (6.0, 6.0, 6.0),
    "cone": (6.0, 8.0, 6.0),
    "wedge": (6.0, 6.0, 6.0),
    "kill": (8.0, 1.0, 8.0),
}

SHAPE_PREFIX = {
    "box": "Box",
    "sphere": "Sphere",
    "cylinder": "Cylinder",
    "cone": "Cone",
    "wedge": "Wedge",
    "kill": "Kill",
}

SHAPE_COLOR = {
    "box": BOX_COLOR,
    "sphere": SPHERE_COLOR,
    "cylinder": CYLINDER_COLOR,
    "cone": CONE_COLOR,
    "wedge": WEDGE_COLOR,
    "kill": KILL_COLOR,
    "start": START_COLOR,
    "end": END_COLOR,
}

LIGHT_DIR = (0.42, 0.88, 0.28)

UNDO_DEPTH = 256

API_BASE = "https://tle.booty-creek.com"
TLEPROJ_EXT = ".tleproj"
