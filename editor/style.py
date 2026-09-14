DARK_STYLESHEET = '''
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 12px;
}

QMainWindow {
    background-color: #1e1e1e;
}

QMainWindow::separator {
    background-color: #2d2d30;
    width: 1px;
    height: 1px;
}

QMenuBar {
    background-color: #2d2d30;
    border-bottom: 1px solid #3e3e42;
    padding: 2px 4px;
    color: #d4d4d4;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #3e3e42;
}

QMenuBar::item:pressed {
    background-color: #094771;
}

QMenu {
    background-color: #252526;
    border: 1px solid #3e3e42;
    padding: 4px;
    color: #d4d4d4;
}

QMenu::item {
    padding: 6px 24px 6px 24px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #6a6a6a;
}

QMenu::separator {
    height: 1px;
    background: #3e3e42;
    margin: 4px 8px;
}

QToolBar {
    background-color: #252526;
    border: none;
    border-bottom: 1px solid #3e3e42;
    padding: 4px 6px;
    spacing: 2px;
}

QToolBar::separator {
    background: #3e3e42;
    width: 1px;
    margin: 4px 6px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 5px;
    color: #cccccc;
}

QToolButton:hover {
    background-color: #3e3e42;
    border-color: #4a4a4e;
}

QToolButton:pressed {
    background-color: #094771;
    border-color: #1177bb;
}

QToolButton:checked {
    background-color: #094771;
    border-color: #1177bb;
    color: #ffffff;
}

QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    border: none;
    font-size: 11px;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 0 8px;
    background: transparent;
}

QStatusBar::item {
    border: none;
}

QDockWidget {
    color: #d4d4d4;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    border: none;
}

QDockWidget::title {
    background-color: #2d2d30;
    border-bottom: 1px solid #3e3e42;
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
    color: #cccccc;
}

QDockWidget::close-button,
QDockWidget::float-button {
    background: transparent;
    border: none;
    padding: 0px;
    icon-size: 12px;
}

QDockWidget::close-button:hover,
QDockWidget::float-button:hover {
    background-color: #3e3e42;
    border-radius: 3px;
}

QGroupBox {
    background-color: #252526;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-weight: 600;
    font-size: 11px;
    color: #9d9d9d;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    top: 2px;
    padding: 0 4px;
    color: #9d9d9d;
    letter-spacing: 0.5px;
}

QLabel {
    background: transparent;
    color: #d4d4d4;
}

QLabel[dim="true"] {
    color: #808080;
}

QLabel[heading="true"] {
    font-size: 13px;
    font-weight: 600;
    color: #e6e6e6;
}

QPushButton {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    padding: 6px 12px;
    color: #d4d4d4;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #3e3e42;
    border-color: #4a4a4e;
}

QPushButton:pressed {
    background-color: #094771;
    border-color: #1177bb;
}

QPushButton:disabled {
    background-color: #252526;
    color: #5a5a5a;
    border-color: #333336;
}

QPushButton[accent="true"] {
    background-color: #0e639c;
    border-color: #1177bb;
    color: #ffffff;
    font-weight: 600;
}

QPushButton[accent="true"]:hover {
    background-color: #1177bb;
}

QPushButton[accent="true"]:pressed {
    background-color: #094771;
}

QPushButton[danger="true"] {
    background-color: #6b2020;
    border-color: #8a2929;
    color: #ffd7d7;
}

QPushButton[danger="true"]:hover {
    background-color: #8a2929;
}

QDoubleSpinBox, QSpinBox, QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    padding: 4px 6px;
    color: #d4d4d4;
    selection-background-color: #094771;
    selection-color: #ffffff;
}

QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {
    border-color: #007acc;
}

QDoubleSpinBox::up-button,
QSpinBox::up-button {
    background-color: #2d2d30;
    border-left: 1px solid #3e3e42;
    border-top-right-radius: 3px;
    width: 14px;
}

QDoubleSpinBox::down-button,
QSpinBox::down-button {
    background-color: #2d2d30;
    border-left: 1px solid #3e3e42;
    border-bottom-right-radius: 3px;
    width: 14px;
}

QDoubleSpinBox::up-button:hover,
QSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover,
QSpinBox::down-button:hover {
    background-color: #3e3e42;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 5px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4f4f4f;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 5px;
    min-width: 20px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4f4f4f;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QToolTip {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    padding: 4px 8px;
}

QDialog {
    background-color: #252526;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

QCheckBox {
    background: transparent;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    background-color: #1e1e1e;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}
'''
