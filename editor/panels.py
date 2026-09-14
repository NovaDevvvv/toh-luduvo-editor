from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from editor.constants import KILL_SHAPE, SHAPES


class AxisSpinRow(QWidget):
    def __init__(self, on_change, minimum=-10000.0, maximum=10000.0, step=0.5):
        super().__init__()
        self._on_change = on_change
        self._block = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._boxes = []
        for i in range(3):
            box = QDoubleSpinBox()
            box.setDecimals(2)
            box.setRange(minimum, maximum)
            box.setSingleStep(step)
            box.setButtonSymbols(QDoubleSpinBox.NoButtons)
            box.setFixedWidth(78)
            box.valueChanged.connect(lambda v, idx=i: self._emit(idx, v))
            layout.addWidget(box)
            self._boxes.append(box)

        layout.addStretch(1)

    def _emit(self, idx, value):
        if self._block:
            return
        if self._on_change is not None:
            self._on_change(idx, value)

    def set_values(self, values):
        self._block = True
        for i, box in enumerate(self._boxes):
            box.setValue(float(values[i]))
        self._block = False

    def set_enabled(self, enabled):
        for box in self._boxes:
            box.setEnabled(enabled)


class MotionEditor(QGroupBox):
    def __init__(self, viewport):
        super().__init__("MOTION")
        self.viewport = viewport
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 14, 10, 10)
        root.setSpacing(8)

        self.enable = QCheckBox("Enabled")
        root.addWidget(self.enable)

        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        labels.setSpacing(4)
        for ch, col in (("X", "#e44c4c"), ("Y", "#66d166"), ("Z", "#4c8cff")):
            lbl = QLabel(ch)
            lbl.setFixedWidth(78)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setStyleSheet(f"color: {col}; font-weight: 600; font-size: 10px;")
            labels.addWidget(lbl)
        labels.addStretch(1)
        root.addLayout(labels)

        self.delta_row = AxisSpinRow(
            lambda a, v: self._on_delta(a, v),
            minimum=-500.0, maximum=500.0, step=1.0,
        )
        root.addWidget(self.delta_row)

        speed_row = QHBoxLayout()
        speed_lbl = QLabel("Speed")
        speed_lbl.setProperty("dim", True)
        speed_row.addWidget(speed_lbl)
        speed_row.addStretch(1)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.1, 500.0)
        self.speed.setSingleStep(0.5)
        self.speed.setDecimals(1)
        self.speed.setFixedWidth(90)
        speed_row.addWidget(self.speed)
        root.addLayout(speed_row)

        phase_row = QHBoxLayout()
        phase_lbl = QLabel("Phase")
        phase_lbl.setProperty("dim", True)
        phase_row.addWidget(phase_lbl)
        phase_row.addStretch(1)
        self.phase_val = QLabel("0.00")
        self.phase_val.setFixedWidth(60)
        self.phase_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        phase_row.addWidget(self.phase_val)
        root.addLayout(phase_row)

        self.phase = QSlider(Qt.Horizontal)
        self.phase.setRange(0, 1000)
        root.addWidget(self.phase)

        hint = QLabel("Drag the endpoint marker in the viewport")
        hint.setProperty("dim", True)
        font = hint.font()
        font.setPointSize(9)
        hint.setFont(font)
        hint.setWordWrap(True)
        root.addWidget(hint)

    def _on_delta(self, axis, value):
        if self._updating:
            return
        obj = self.viewport.get_selected()
        if obj is None or obj.locked:
            return
        m = obj.motion
        if axis == 0:
            m.dx = float(value)
        elif axis == 1:
            m.dy = float(value)
        else:
            m.dz = float(value)
        self.viewport.update()


class PropertiesPanel(QWidget):
    def __init__(self, viewport):
        super().__init__()
        self.viewport = viewport
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        heading = QLabel("Properties")
        heading.setProperty("heading", True)
        root.addWidget(heading)

        self.name_label = QLabel("No selection")
        self.name_label.setProperty("dim", True)
        root.addWidget(self.name_label)

        self.kind_label = QLabel("")
        self.kind_label.setProperty("dim", True)
        root.addWidget(self.kind_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3e3e42; background-color: #3e3e42; max-height:1px;")
        root.addWidget(line)

        self.pos_row = AxisSpinRow(lambda a, v: self._emit("position", a, v))
        self.size_row = AxisSpinRow(lambda a, v: self._emit("scale", a, v))
        self.rot_row = AxisSpinRow(lambda a, v: self._emit("rotation", a, v))

        root.addWidget(self._group_label("Position"))
        root.addWidget(self.pos_row)
        root.addWidget(self._group_label("Size"))
        root.addWidget(self.size_row)
        root.addWidget(self._group_label("Rotation (deg)"))
        root.addWidget(self.rot_row)

        self.motion_editor = MotionEditor(viewport)
        root.addWidget(self.motion_editor)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #3e3e42; background-color: #3e3e42; max-height:1px;")
        root.addWidget(line2)

        height_row = QHBoxLayout()
        height_row.setSpacing(8)
        lbl = QLabel("Level height")
        lbl.setProperty("dim", True)
        height_row.addWidget(lbl)
        self.height_label = QLabel("")
        self.height_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        height_row.addWidget(self.height_label, 1)
        root.addLayout(height_row)

        self.height_slider = QSlider(Qt.Horizontal)
        self.height_slider.setRange(10, 200)
        self.height_slider.setValue(40)
        self.height_slider.valueChanged.connect(self._on_height)
        root.addWidget(self.height_slider)

        root.addStretch(1)

        self.refresh()

    def _group_label(self, text):
        lbl = QLabel(text.upper())
        lbl.setProperty("dim", True)
        font = lbl.font()
        font.setPointSize(9)
        font.setBold(True)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #808080; letter-spacing: 0.6px;")
        return lbl

    def _emit(self, field, axis, value):
        if self._updating:
            return
        self.viewport.apply_property(field, axis, value)

    def _on_height(self, value):
        if self._updating:
            return
        self.viewport.set_height(float(value))

    def refresh(self):
        self._updating = True

        sel = self.viewport.get_selected()
        level = self.viewport.level

        if sel is None or sel.locked:
            self.name_label.setText("No selection")
            self.kind_label.setText("")
            self.pos_row.set_values((0.0, 0.0, 0.0))
            self.size_row.set_values((0.0, 0.0, 0.0))
            self.rot_row.set_values((0.0, 0.0, 0.0))
            self.pos_row.set_enabled(False)
            self.size_row.set_enabled(False)
            self.rot_row.set_enabled(False)
            self.motion_editor.setEnabled(False)
        else:
            self.name_label.setText(sel.name)
            self.kind_label.setText(sel.kind.upper())
            self.pos_row.set_values(sel.position)
            self.size_row.set_values(sel.scale)
            self.rot_row.set_values(sel.rotation)
            self.pos_row.set_enabled(True)
            self.size_row.set_enabled(True)
            self.rot_row.set_enabled(True)
            self.motion_editor.setEnabled(True)

            m = sel.motion
            self.motion_editor.enable.setChecked(m.enabled)
            self.motion_editor.delta_row.set_values((m.dx, m.dy, m.dz))
            self.motion_editor.speed.setValue(m.speed)
            self.motion_editor.phase.setValue(int(m.phase * 1000))
            self.motion_editor.phase_val.setText(f"{m.phase:.2f}")

        self.height_slider.setValue(int(level.height))
        self.height_label.setText(f"{level.height:.0f}")

        self._updating = False


class ToolsPanel(QWidget):
    def __init__(self, viewport):
        super().__init__()
        self.viewport = viewport

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        heading = QLabel("Create")
        heading.setProperty("heading", True)
        root.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(6)

        shapes = list(SHAPES) + [KILL_SHAPE]
        for i, (kind, label) in enumerate(shapes):
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if kind == "kill":
                btn.setProperty("danger", True)
            btn.clicked.connect(lambda _=False, k=kind: viewport.add_shape_center(k))
            grid.addWidget(btn, i // 2, i % 2)

        root.addLayout(grid)

        root.addSpacing(6)

        heading2 = QLabel("Layout")
        heading2.setProperty("heading", True)
        root.addWidget(heading2)

        reset_btn = QPushButton("Reset level")
        reset_btn.clicked.connect(viewport.reset_level)
        root.addWidget(reset_btn)

        root.addStretch(1)


def _wire_motion_editor(editor, viewport):
    def on_enable(checked):
        if editor._updating:
            return
        obj = viewport.get_selected()
        if obj is None or obj.locked:
            return
        obj.motion.enabled = bool(checked)
        obj.motion.phase = 0.0
        viewport.levelChanged.emit()
        viewport.update()

    def on_speed(value):
        if editor._updating:
            return
        obj = viewport.get_selected()
        if obj is None or obj.locked:
            return
        obj.motion.speed = float(value)
        viewport.update()

    def on_phase(value):
        if editor._updating:
            return
        obj = viewport.get_selected()
        if obj is None or obj.locked:
            return
        obj.motion.phase = value / 1000.0
        editor.phase_val.setText(f"{obj.motion.phase:.2f}")
        viewport.update()

    editor.enable.toggled.connect(on_enable)
    editor.speed.valueChanged.connect(on_speed)
    editor.phase.valueChanged.connect(on_phase)
