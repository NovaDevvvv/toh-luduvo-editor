import os
import sys


FILES = {}


FILES["editor/api.py"] = r"""
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
"""


FILES["editor/export.py"] = r"""
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
"""


FILES["editor/export_dialog.py"] = r"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from editor import api
from editor.constants import API_BASE
from editor.export import (
    compact_object,
    export_level,
    read_sidecar,
    write_sidecar,
)


class ExportDialog(QDialog):
    def __init__(self, parent, level):
        super().__init__(parent)
        self.level = level
        self.exported_path = None
        self.submitted_url = None
        self.submitted_project_id = None
        self.submitted_revision = None

        self.setWindowTitle("Export Level")
        self.setMinimumWidth(480)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        heading = QLabel("Export Level")
        heading.setProperty("heading", True)
        root.addWidget(heading)

        sub = QLabel(
            "Saves a JSON file to exports/ and optionally uploads it to "
            + API_BASE
        )
        sub.setProperty("dim", True)
        sub.setWordWrap(True)
        root.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        self.level_edit = QLineEdit()
        self.level_edit.setPlaceholderText("e.g. Lava Gauntlet")
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Your name")

        form.addRow("Level name", self.level_edit)
        form.addRow("Author", self.author_edit)
        root.addLayout(form)

        self.upload_check = QCheckBox("Submit to server")
        self.upload_check.setChecked(True)
        root.addWidget(self.upload_check)

        self.status = QLabel("")
        self.status.setProperty("dim", True)
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.url_label = QLabel("")
        self.url_label.setProperty("dim", True)
        self.url_label.setWordWrap(True)
        self.url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.url_label)

        buttons = QDialogButtonBox()
        self.export_btn = buttons.addButton("Export", QDialogButtonBox.AcceptRole)
        self.export_btn.setProperty("accent", True)
        buttons.addButton("Close", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._on_export)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.level_edit.setFocus()
        self.level_edit.returnPressed.connect(self._on_export)
        self.author_edit.returnPressed.connect(self._on_export)

    def _on_export(self):
        name = self.level_edit.text().strip()
        author = self.author_edit.text().strip()

        if not name:
            self._fail("Level name is required.")
            return
        if not author:
            self._fail("Author name is required.")
            return

        try:
            path = export_level(
                name,
                author,
                self.level.height,
                self.level.objects,
                radius=self.level.RADIUS,
                segments=self.level.PARTS_PER_LAYER,
            )
        except Exception as exc:
            self._fail(f"Local export failed: {exc}")
            return

        self.exported_path = path
        self.status.setText(f"Saved  {path}")
        self.status.setStyleSheet("color: #4ec86e;")

        if not self.upload_check.isChecked():
            return

        sidecar = read_sidecar(name)
        project_id = sidecar.get("projectId") if sidecar else None

        objects_payload = [compact_object(o) for o in self.level.objects]

        try:
            payload = api.submit_level(
                project_id=project_id,
                height=self.level.height,
                radius=self.level.RADIUS,
                segments=self.level.PARTS_PER_LAYER,
                objects=objects_payload,
                name=name,
                author=author,
            )
        except api.ApiError as exc:
            self._fail(f"Upload failed: {exc.message}")
            return

        project = payload.get("project") or {}
        revision = payload.get("revision") or {}
        new_pid = project.get("projectId") or project_id
        new_rev = revision.get("revision") or 0

        if new_pid:
            try:
                write_sidecar(name, new_pid, author, new_rev, name)
            except Exception:
                pass

        url = api.view_url(new_pid, new_rev) if new_pid else None
        self.submitted_url = url
        self.submitted_project_id = new_pid
        self.submitted_revision = new_rev

        if payload.get("created"):
            self.status.setText(f"Project created  ·  revision {new_rev}")
        else:
            self.status.setText(f"Revision {new_rev} uploaded")
        self.status.setStyleSheet("color: #4ec86e;")

        if url:
            self.url_label.setText(url)

    def _fail(self, message):
        self.status.setText(message)
        self.status.setStyleSheet("color: #f48771;")
"""


FILES["editor/web_dialog.py"] = r"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from editor import api


class WebImportDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.loaded_payload = None
        self.setWindowTitle("Import from web")
        self.setMinimumSize(560, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        heading = QLabel("Import from web")
        heading.setProperty("heading", True)
        root.addWidget(heading)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_lbl = QLabel("Author")
        filter_lbl.setProperty("dim", True)
        filter_row.addWidget(filter_lbl)
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("filter by author (optional)")
        filter_row.addWidget(self.author_edit, 1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        filter_row.addWidget(refresh_btn)
        root.addLayout(filter_row)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_accept)
        root.addWidget(self.list, 1)

        self.status = QLabel("")
        self.status.setProperty("dim", True)
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        buttons = QDialogButtonBox()
        open_btn = buttons.addButton("Open", QDialogButtonBox.AcceptRole)
        open_btn.setProperty("accent", True)
        buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.author_edit.returnPressed.connect(self.refresh)

        try:
            self.refresh()
        except Exception as exc:
            self.status.setText(f"Error: {exc}")

    def refresh(self):
        self.list.clear()
        self.status.setText("Loading…")
        author = self.author_edit.text().strip() or None
        try:
            payload = api.list_projects(author=author, limit=50)
        except api.ApiError as exc:
            self.status.setText(f"Error: {exc.message}")
            return

        items = payload.get("items") or []
        if not items:
            self.status.setText("No projects found.")
            return

        for p in items:
            label = (
                f"{p.get('name', '(untitled)')}   ·   "
                f"{p.get('author', '?')}   ·   "
                f"rev {p.get('revision', 0)}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, p.get("projectId"))
            self.list.addItem(item)

        self.status.setText(
            f"{len(items)} project(s)   ·   total {payload.get('total', 0)}"
        )

    def _on_accept(self, *_):
        item = self.list.currentItem()
        if item is None:
            return
        project_id = item.data(Qt.UserRole)
        if not project_id:
            return
        self.status.setText(f"Loading {project_id}…")
        try:
            payload = api.view_level(project_id)
        except api.ApiError as exc:
            self.status.setText(f"Error: {exc.message}")
            return
        self.loaded_payload = payload
        self.accept()
"""


FILES["editor/main_window.py"] = r"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from editor.constants import APP_NAME, APP_VERSION, SIDEBAR_WIDTH
from editor.export_dialog import ExportDialog
from editor.export import load_level, level_from_server
from editor.gl_viewport import (
    GLViewport,
    TOOL_MOVE,
    TOOL_ROTATE,
    TOOL_SCALE,
    TOOL_SELECT,
)
from editor.icons import move_icon, rotate_icon, scale_icon, select_icon
from editor.panels import PropertiesPanel, ToolsPanel, _wire_motion_editor
from editor.web_dialog import WebImportDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  {APP_VERSION}")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        self.viewport = GLViewport(self)
        self.setCentralWidget(self.viewport)

        self._build_menu()
        self._build_toolbar()
        self._build_docks()
        self._build_statusbar()
        self._wire_signals()

    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        export_act = QAction("Export to JSON", self)
        export_act.setShortcut(QKeySequence("Ctrl+S"))
        export_act.triggered.connect(self._on_export)
        file_menu.addAction(export_act)

        import_act = QAction("Import JSON", self)
        import_act.setShortcut(QKeySequence("Ctrl+O"))
        import_act.triggered.connect(self._on_import)
        file_menu.addAction(import_act)

        web_act = QAction("Import from web…", self)
        web_act.setShortcut(QKeySequence("Ctrl+Shift+O"))
        web_act.triggered.connect(self._on_import_web)
        file_menu.addAction(web_act)

        file_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        edit_menu = menubar.addMenu("&Edit")

        undo_act = QAction("Undo", self)
        undo_act.setShortcut(QKeySequence("Ctrl+Z"))
        undo_act.triggered.connect(self.viewport.undo)
        edit_menu.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        redo_act.triggered.connect(self.viewport.redo)
        edit_menu.addAction(redo_act)

        edit_menu.addSeparator()

        copy_act = QAction("Copy", self)
        copy_act.setShortcut(QKeySequence("Ctrl+C"))
        copy_act.triggered.connect(self.viewport.copy_selected)
        edit_menu.addAction(copy_act)

        paste_act = QAction("Paste", self)
        paste_act.setShortcut(QKeySequence("Ctrl+V"))
        paste_act.triggered.connect(self.viewport.paste_clipboard)
        edit_menu.addAction(paste_act)

        delete_act = QAction("Delete", self)
        delete_act.setShortcut(QKeySequence("Del"))
        delete_act.triggered.connect(self.viewport.delete_selected)
        edit_menu.addAction(delete_act)

        view_menu = menubar.addMenu("&View")

        for label, view in (
            ("Front View", "front"),
            ("Right View", "right"),
            ("Top View", "top"),
            ("Perspective", "persp"),
        ):
            act = QAction(label, self)
            act.triggered.connect(lambda _=False, v=view: self._set_view(v))
            view_menu.addAction(act)

        view_menu.addSeparator()

        reset_act = QAction("Reset Level", self)
        reset_act.triggered.connect(self.viewport.reset_level)
        view_menu.addAction(reset_act)

        help_menu = menubar.addMenu("&Help")

        about_act = QAction("About", self)
        about_act.triggered.connect(self._on_about)
        help_menu.addAction(about_act)

    def _build_toolbar(self):
        bar = QToolBar("Tools")
        bar.setMovable(False)
        self.addToolBar(bar)

        self.tool_actions = {}

        tool_defs = (
            (TOOL_MOVE, "Move  (G)", move_icon()),
            (TOOL_SCALE, "Scale  (S)", scale_icon()),
            (TOOL_ROTATE, "Rotate  (R)", rotate_icon()),
            (TOOL_SELECT, "Select  (Q)", select_icon()),
        )

        for tool, label, icon in tool_defs:
            act = QAction(icon, label, self)
            act.setCheckable(True)
            act.setToolTip(label)
            act.triggered.connect(lambda _=False, t=tool: self.viewport.set_tool(t))
            bar.addAction(act)
            self.tool_actions[tool] = act

        self.tool_actions[TOOL_MOVE].setChecked(True)

        bar.addSeparator()

        for label, view in (
            ("Front", "front"),
            ("Right", "right"),
            ("Top", "top"),
            ("Persp", "persp"),
        ):
            act = QAction(label, self)
            act.triggered.connect(lambda _=False, v=view: self._set_view(v))
            bar.addAction(act)

        bar.addSeparator()

        undo_act = QAction("Undo", self)
        undo_act.triggered.connect(self.viewport.undo)
        bar.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.triggered.connect(self.viewport.redo)
        bar.addAction(redo_act)

        bar.addSeparator()

        reset_act = QAction("Reset", self)
        reset_act.triggered.connect(self.viewport.reset_level)
        bar.addAction(reset_act)

        export_act = QAction("Export", self)
        export_act.triggered.connect(self._on_export)
        bar.addAction(export_act)

        web_act = QAction("Web", self)
        web_act.triggered.connect(self._on_import_web)
        bar.addAction(web_act)

    def _build_docks(self):
        props = PropertiesPanel(self.viewport)
        dock_props = QDockWidget("PROPERTIES", self)
        dock_props.setWidget(props)
        dock_props.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        dock_props.setMinimumWidth(SIDEBAR_WIDTH)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_props)
        self.props_panel = props

        _wire_motion_editor(props.motion_editor, self.viewport)

        tools = ToolsPanel(self.viewport)
        dock_tools = QDockWidget("CREATE", self)
        dock_tools.setWidget(tools)
        dock_tools.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        dock_tools.setMinimumWidth(SIDEBAR_WIDTH)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_tools)
        self.tools_panel = tools

    def _build_statusbar(self):
        bar = self.statusBar()
        self.status_left = QLabel("Ready")
        self.status_right = QLabel("")
        bar.addWidget(self.status_left, 1)
        bar.addPermanentWidget(self.status_right)
        self._on_level_changed(None)

    def _wire_signals(self):
        self.viewport.selectionChanged.connect(self._on_selection)
        self.viewport.levelChanged.connect(self._on_level_changed)
        self.viewport.toolChanged.connect(self._on_tool_changed)
        self.viewport.statusMessage.connect(self._on_status_message)

    def _on_status_message(self, text):
        self.statusBar().showMessage(text, 4000)

    def _on_selection(self, obj):
        self.props_panel.refresh()
        if obj is None:
            self.status_left.setText("No selection")
        else:
            self.status_left.setText(f"Selected: {obj.name}  ({obj.kind})")

    def _on_level_changed(self, _):
        self.props_panel.refresh()
        level = self.viewport.level
        self.status_right.setText(
            f"Objects: {len(level.objects)}   "
            f"Height: {level.height:.0f}   "
            f"Radius: {level.RADIUS:.0f}"
        )

    def _on_tool_changed(self, tool):
        for t, act in self.tool_actions.items():
            act.setChecked(t == tool)

    def _set_view(self, name):
        self.viewport.camera.set_view(name)
        self.viewport.update()

    def _on_export(self):
        dialog = ExportDialog(self, self.viewport.level)
        if dialog.exec():
            if dialog.submitted_url:
                self.statusBar().showMessage(
                    f"Uploaded revision {dialog.submitted_revision} → {dialog.submitted_url}",
                    6000,
                )
            elif dialog.exported_path:
                self.statusBar().showMessage(
                    f"Exported to {dialog.exported_path}", 4000
                )

    def _apply_level(self, data, source_label):
        self.viewport.history.push(self.viewport.level)
        self.viewport.level.reset()
        self.viewport.level.set_height(float(data.get("height", 40.0)))
        self.viewport.level.objects = data.get("objects", [])
        self.viewport._set_selection(None)
        self.viewport.levelChanged.emit(None)
        self.viewport.update()

        self.statusBar().showMessage(
            f"{source_label}   ·   {len(data.get('objects', []))} objects",
            5000,
        )

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Level", "exports", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            data = load_level(path)
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self._apply_level(data, f"Imported {path}")

    def _on_import_web(self):
        dialog = WebImportDialog(self)
        if not dialog.exec():
            return
        if dialog.loaded_payload is None:
            return
        try:
            data = level_from_server(dialog.loaded_payload)
        except Exception as exc:
            QMessageBox.warning(self, "Load failed", str(exc))
            return
        pid = data.get("project_id") or "?"
        rev = data.get("revision") or "?"
        self._apply_level(data, f"Loaded {pid} (rev {rev})")

    def _on_about(self):
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>Version {APP_VERSION}</p>"
            "<p>Single-layer tower level editor.<br>"
            "Right-click a part for motion options.<br>"
            "MMB orbits, Shift+MMB pans, wheel zooms.<br><br>"
            "Cloud sync: tle.booty-creek.com</p>",
        )
"""


def patch_constants(root):
    path = os.path.join(root, "editor", "constants.py")
    if not os.path.isfile(path):
        raise SystemExit(f"constants.py not found at {path}")

    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()

    if "API_BASE" in src:
        return

    if not src.endswith("\n"):
        src += "\n"

    src += (
        "\n"
        "API_BASE = \"https://tle.booty-creek.com\"\n"
        "TLEPROJ_EXT = \".tleproj\"\n"
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src)


def write_project(root):
    for rel, content in FILES.items():
        full = os.path.join(root, rel)
        directory = os.path.dirname(full)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content.lstrip("\n"))
    patch_constants(root)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    write_project(root)
    print(f"Updated {len(FILES)} files in {os.path.abspath(root)}")
    print()
    print("Changes:")
    print("  + editor/api.py            - HTTP client for tle.booty-creek.com")
    print("  + editor/web_dialog.py     - browse & load projects from the server")
    print("  ~ editor/export.py         - writes .tleproj sidecar, reads server payloads")
    print("  ~ editor/export_dialog.py  - checkbox to upload on export")
    print("  ~ editor/main_window.py    - File → Import from web…")
    print("  ~ editor/constants.py      - API_BASE + TLEPROJ_EXT appended")
    print()
    print("Run:  python main.py")


if __name__ == "__main__":
    main()