import json
import urllib.error
import urllib.parse
import urllib.request

from editor.constants import API_BASE


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def _request(method, path, body=None, timeout=25):
    url = API_BASE.rstrip("/") + path
    data = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "tle-editor/2.0",
    }
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"raw": raw}
    except urllib.error.HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8")
        except Exception:
            pass
        code = "http_error"
        message = f"HTTP {exc.code}"
        details = None
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict) and "error" in payload:
                e = payload["error"]
                code = e.get("code", code)
                message = e.get("message", message)
                details = e.get("details")
        except Exception:
            pass
        raise ApiError(exc.code, code, message, details)
    except urllib.error.URLError as exc:
        raise ApiError(0, "network_error", str(exc.reason or exc))
    except Exception as exc:
        raise ApiError(0, "request_failed", str(exc))


def create_project(name, author, description=None):
    body = {"name": name, "author": author}
    if description:
        body["description"] = description
    _, payload = _request("POST", "/api/v1/project", body)
    return payload


def submit_level(project_id, height, radius, segments, objects,
                 name=None, author=None, message=None):
    body = {
        "height": height,
        "radius": radius,
        "segments": segments,
        "objects": objects,
    }
    if project_id:
        body["projectId"] = project_id
    if name:
        body["name"] = name
    if author:
        body["author"] = author
    if message:
        body["message"] = message
    _, payload = _request("POST", "/api/v1/submit", body)
    return payload


def view_level(project_id, revision=None):
    query = {"id": project_id}
    if revision is not None:
        query["revision"] = str(revision)
    _, payload = _request("GET", "/api/v1/view?" + urllib.parse.urlencode(query))
    return payload


def list_projects(author=None, limit=30, offset=0):
    query = {"limit": str(limit), "offset": str(offset)}
    if author:
        query["author"] = author
    _, payload = _request("GET", "/api/v1/list?" + urllib.parse.urlencode(query))
    return payload


def view_url(project_id, revision=None):
    base = API_BASE.rstrip("/") + "/api/v1/view?id=" + urllib.parse.quote(project_id)
    if revision is not None:
        base += "&revision=" + str(revision)
    return base
