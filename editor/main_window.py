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
