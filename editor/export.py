import json
import os
import re
from datetime import datetime, timezone

from editor.constants import API_BASE, TLEPROJ_EXT


EXPORT_DIR = "exports"


def _sanitize(name):
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "level"


def _r(v, n=3):
    if isinstance(v, (int, float)):
        return round(float(v), n)
    return v


def _rlist(lst):
    return [_r(x) for x in lst]


def _color_hex(c):
    r = max(0, min(255, int(round(c[0] * 255))))
    g = max(0, min(255, int(round(c[1] * 255))))
    b = max(0, min(255, int(round(c[2] * 255))))
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def compact_object(obj):
    md = obj.motion.to_dict()
    d = {
        "n": obj.name,
        "p": _rlist(obj.position),
        "s": _rlist(obj.scale),
        "r": _rlist(obj.rotation),
        "c": _color_hex(obj.color),
    }
    if obj.kind != "box":
        d["k"] = obj.kind
    if md is not None:
        if not md.get("enabled", False):
            md = {k: v for k, v in md.items() if k != "enabled"}
        d["m"] = {k: _r(v) for k, v in md.items()}
    return d


def make_payload(level_name, author, height, objects, radius=70.0, segments=16):
    return {
        "schema": 3,
        "name": level_name,
        "author": author,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "height": _r(height),
        "radius": _r(radius),
        "segments": int(segments),
        "objects": [compact_object(o) for o in objects],
    }


def sidecar_path(name, out_dir=EXPORT_DIR):
    safe = _sanitize(name)
    return os.path.join(out_dir, safe + TLEPROJ_EXT)


def read_sidecar(name, out_dir=EXPORT_DIR):
    path = sidecar_path(name, out_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def write_sidecar(name, project_id, author, revision, level_name, out_dir=EXPORT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    path = sidecar_path(name, out_dir)
    data = {
        "format": "tleproj",
        "version": 1,
        "projectId": project_id,
        "name": level_name,
        "author": author,
        "revision": revision,
        "apiBase": API_BASE,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return path


def export_level(level_name, author, height, objects,
                 radius=70.0, segments=16, out_dir=EXPORT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    safe = _sanitize(level_name)
    path = os.path.join(out_dir, safe + ".json")
    payload = make_payload(level_name, author, height, objects,
                           radius=radius, segments=segments)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, separators=(",", ":"))
    return path


def load_level(path):
    from editor.objects import Object3D
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    objects = [Object3D.from_dict(d) for d in payload.get("objects", [])]
    return {
        "height": float(payload.get("height", 40.0)),
        "radius": float(payload.get("radius", 70.0)),
        "segments": int(payload.get("segments", 16)),
        "objects": objects,
        "name": payload.get("name") or payload.get("level_name") or "level",
        "author": payload.get("author") or "",
        "project_id": None,
        "revision": None,
    }


def level_from_server(payload):
    from editor.objects import Object3D
    level = payload.get("level", {}) or {}
    objects = [Object3D.from_dict(d) for d in level.get("objects", [])]
    project = payload.get("project", {}) or {}
    revision = payload.get("revision", {}) or {}
    return {
        "height": float(level.get("height", 40.0)),
        "radius": float(level.get("radius", 70.0)),
        "segments": int(level.get("segments", 16)),
        "objects": objects,
        "name": project.get("name") or "level",
        "author": project.get("author") or "",
        "project_id": project.get("projectId"),
        "revision": revision.get("revision"),
    }
