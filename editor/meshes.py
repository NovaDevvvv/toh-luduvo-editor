import math


def box_faces(scale):
    hx, hy, hz = scale[0] / 2.0, scale[1] / 2.0, scale[2] / 2.0
    A = (-hx, -hy, -hz)
    B = (hx, -hy, -hz)
    C = (hx, hy, -hz)
    D = (-hx, hy, -hz)
    E = (-hx, -hy, hz)
    F = (hx, -hy, hz)
    G = (hx, hy, hz)
    H = (-hx, hy, hz)
    return (
        (A, B, C, D),
        (E, H, G, F),
        (A, E, F, B),
        (D, C, G, H),
        (A, D, H, E),
        (B, F, G, C),
    )


def sphere_faces(scale, lat=12, lon=16):
    rx, ry, rz = scale[0] / 2.0, scale[1] / 2.0, scale[2] / 2.0
    faces = []
    for i in range(lat):
        t1 = math.pi * i / lat
        t2 = math.pi * (i + 1) / lat
        st1, ct1 = math.sin(t1), math.cos(t1)
        st2, ct2 = math.sin(t2), math.cos(t2)
        for j in range(lon):
            p1 = math.tau * j / lon
            p2 = math.tau * (j + 1) / lon
            cp1, sp1 = math.cos(p1), math.sin(p1)
            cp2, sp2 = math.cos(p2), math.sin(p2)
            a = (rx * st1 * cp1, ry * ct1, rz * st1 * sp1)
            b = (rx * st1 * cp2, ry * ct1, rz * st1 * sp2)
            c = (rx * st2 * cp2, ry * ct2, rz * st2 * sp2)
            d = (rx * st2 * cp1, ry * ct2, rz * st2 * sp1)
            if i == 0:
                faces.append((a, c, d))
            elif i == lat - 1:
                faces.append((a, b, d))
            else:
                faces.append((a, b, c, d))
    return faces


def cylinder_faces(scale, segs=28):
    rx, rz = scale[0] / 2.0, scale[2] / 2.0
    hy = scale[1] / 2.0
    faces = []
    for i in range(segs):
        a1 = math.tau * i / segs
        a2 = math.tau * (i + 1) / segs
        c1, s1 = math.cos(a1), math.sin(a1)
        c2, s2 = math.cos(a2), math.sin(a2)
        p1 = (rx * c1, -hy, rz * s1)
        p2 = (rx * c2, -hy, rz * s2)
        p3 = (rx * c2, hy, rz * s2)
        p4 = (rx * c1, hy, rz * s1)
        faces.append((p1, p2, p3, p4))
    top_c = (0.0, hy, 0.0)
    bot_c = (0.0, -hy, 0.0)
    for i in range(segs):
        a1 = math.tau * i / segs
        a2 = math.tau * (i + 1) / segs
        c1, s1 = math.cos(a1), math.sin(a1)
        c2, s2 = math.cos(a2), math.sin(a2)
        tp1 = (rx * c1, hy, rz * s1)
        tp2 = (rx * c2, hy, rz * s2)
        bp1 = (rx * c1, -hy, rz * s1)
        bp2 = (rx * c2, -hy, rz * s2)
        faces.append((top_c, tp1, tp2))
        faces.append((bot_c, bp2, bp1))
    return faces


def cone_faces(scale, segs=28):
    rx, rz = scale[0] / 2.0, scale[2] / 2.0
    hy = scale[1] / 2.0
    faces = []
    apex = (0.0, hy, 0.0)
    bot_c = (0.0, -hy, 0.0)
    for i in range(segs):
        a1 = math.tau * i / segs
        a2 = math.tau * (i + 1) / segs
        c1, s1 = math.cos(a1), math.sin(a1)
        c2, s2 = math.cos(a2), math.sin(a2)
        p1 = (rx * c1, -hy, rz * s1)
        p2 = (rx * c2, -hy, rz * s2)
        faces.append((apex, p1, p2))
        faces.append((bot_c, p2, p1))
    return faces


def wedge_faces(scale):
    hx, hy, hz = scale[0] / 2.0, scale[1] / 2.0, scale[2] / 2.0
    A = (-hx, -hy, -hz)
    B = (hx, -hy, -hz)
    C = (hx, -hy, hz)
    D = (-hx, -hy, hz)
    E = (-hx, hy, -hz)
    F = (-hx, hy, hz)
    return (
        (A, B, C, D),
        (A, E, F, D),
        (A, B, E),
        (B, C, F, E),
        (D, F, C),
    )


def faces_for(kind, scale):
    if kind == "sphere":
        return sphere_faces(scale)
    if kind == "cylinder":
        return cylinder_faces(scale)
    if kind == "cone":
        return cone_faces(scale)
    if kind == "wedge":
        return wedge_faces(scale)
    return box_faces(scale)
