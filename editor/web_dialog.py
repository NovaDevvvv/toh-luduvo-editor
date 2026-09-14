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
