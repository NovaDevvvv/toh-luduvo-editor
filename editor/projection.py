import math

from editor.math3d import v_cross, v_norm, v_sub


def screen_to_ray(mx, my, cam, vw, vh):
    cam_pos = cam.position()
    fwd = v_norm(v_sub(cam.target, cam_pos))
    right = v_norm(v_cross(fwd, (0.0, 1.0, 0.0)))
    up = v_cross(right, fwd)

    ndc_x = (mx / vw) * 2.0 - 1.0
    ndc_y = 1.0 - (my / vh) * 2.0
    tan_half = math.tan(math.radians(cam.fov) * 0.5)
    aspect = (vw / vh) if vh else 1.0

    sx = ndc_x * tan_half * aspect
    sy = ndc_y * tan_half
    direction = (
        right[0] * sx + up[0] * sy + fwd[0],
        right[1] * sx + up[1] * sy + fwd[1],
        right[2] * sx + up[2] * sy + fwd[2],
    )
    return list(cam_pos), v_norm(direction)


def project(point, cam, vw, vh):
    cam_pos = cam.position()
    fwd = v_norm(v_sub(cam.target, cam_pos))
    right = v_norm(v_cross(fwd, (0.0, 1.0, 0.0)))
    up = v_cross(right, fwd)

    rel = v_sub(point, cam_pos)
    x = rel[0] * right[0] + rel[1] * right[1] + rel[2] * right[2]
    y = rel[0] * up[0] + rel[1] * up[1] + rel[2] * up[2]
    z = rel[0] * fwd[0] + rel[1] * fwd[1] + rel[2] * fwd[2]
    if z <= 0.01:
        return None

    tan_half = math.tan(math.radians(cam.fov) * 0.5)
    aspect = (vw / vh) if vh else 1.0
    ndc_x = x / (z * tan_half * aspect)
    ndc_y = y / (z * tan_half)
    return ((ndc_x + 1.0) * 0.5 * vw, (1.0 - ndc_y) * 0.5 * vh)


def closest_t_on_axis(ray_o, ray_d, line_p, line_d):
    d0 = v_norm(ray_d)
    d1 = v_norm(line_d)
    b = d0[0] * d1[0] + d0[1] * d1[1] + d0[2] * d1[2]
    r = v_sub(line_p, ray_o)
    d = d0[0] * r[0] + d0[1] * r[1] + d0[2] * r[2]
    e = d1[0] * r[0] + d1[1] * r[1] + d1[2] * r[2]
    denom = 1.0 - b * b
    if abs(denom) < 1e-6:
        return 0.0
    return (b * d - e) / denom


def seg_dist_2d(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


def ray_intersect_plane_y(ray_o, ray_d, y):
    if abs(ray_d[1]) < 1e-6:
        return None
    t = (y - ray_o[1]) / ray_d[1]
    if t < 0.0:
        return None
    return (ray_o[0] + ray_d[0] * t, y, ray_o[2] + ray_d[2] * t)


def ray_intersect_plane(ray_o, ray_d, plane_p, plane_n):
    denom = (ray_d[0] * plane_n[0] +
             ray_d[1] * plane_n[1] +
             ray_d[2] * plane_n[2])
    if abs(denom) < 1e-6:
        return None
    t = ((plane_p[0] - ray_o[0]) * plane_n[0] +
         (plane_p[1] - ray_o[1]) * plane_n[1] +
         (plane_p[2] - ray_o[2]) * plane_n[2]) / denom
    if t < 0.0:
        return None
    return (
        ray_o[0] + ray_d[0] * t,
        ray_o[1] + ray_d[1] * t,
        ray_o[2] + ray_d[2] * t,
    )
