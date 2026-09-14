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
