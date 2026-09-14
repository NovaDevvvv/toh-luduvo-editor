import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _new_pixmap(size):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    return pix


def _setup(painter, color):
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)


def move_icon(size=20, color="#d4d4d4"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    _setup(p, color)
    c = size / 2.0
    a = size * 0.33
    t = size * 0.11

    p.drawLine(QPointF(c, c - a), QPointF(c, c + a))
    p.drawLine(QPointF(c - a, c), QPointF(c + a, c))

    p.drawLine(QPointF(c, c - a), QPointF(c - t, c - a + t))
    p.drawLine(QPointF(c, c - a), QPointF(c + t, c - a + t))
    p.drawLine(QPointF(c, c + a), QPointF(c - t, c + a - t))
    p.drawLine(QPointF(c, c + a), QPointF(c + t, c + a - t))
    p.drawLine(QPointF(c - a, c), QPointF(c - a + t, c - t))
    p.drawLine(QPointF(c - a, c), QPointF(c - a + t, c + t))
    p.drawLine(QPointF(c + a, c), QPointF(c + a - t, c - t))
    p.drawLine(QPointF(c + a, c), QPointF(c + a - t, c + t))

    p.end()
    return QIcon(pix)


def scale_icon(size=20, color="#d4d4d4"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    _setup(p, color)
    pad = size * 0.24
    a = QPointF(pad, pad)
    b = QPointF(size - pad, pad)
    c = QPointF(size - pad, size - pad)
    d = QPointF(pad, size - pad)

    p.drawLine(a, b)
    p.drawLine(b, c)
    p.drawLine(c, d)
    p.drawLine(d, a)

    dot = size * 0.06
    for pt in (a, b, c, d):
        p.drawRect(QRectF(pt.x() - dot, pt.y() - dot, dot * 2, dot * 2))

    p.end()
    return QIcon(pix)


def rotate_icon(size=20, color="#d4d4d4"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    _setup(p, color)
    c = size / 2.0
    r = size * 0.30

    rect = QRectF(c - r, c - r, r * 2, r * 2)
    p.drawArc(rect, 40 * 16, 280 * 16)

    t = math.radians(40)
    tip = QPointF(c + math.cos(t) * r, c - math.sin(t) * r)
    l = size * 0.09
    p.drawLine(tip, QPointF(tip.x() - l, tip.y() - l * 0.2))
    p.drawLine(tip, QPointF(tip.x() + l * 0.2, tip.y() + l))

    p.end()
    return QIcon(pix)


def select_icon(size=20, color="#d4d4d4"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    _setup(p, color)

    pad = size * 0.22
    pts = [
        QPointF(pad, pad),
        QPointF(pad, size - pad),
        QPointF(size * 0.46, size * 0.62),
        QPointF(size * 0.64, size - pad * 0.9),
        QPointF(size * 0.78, size * 0.82),
        QPointF(size * 0.58, size * 0.54),
        QPointF(size - pad, size * 0.54),
    ]
    for i in range(len(pts) - 1):
        p.drawLine(pts[i], pts[i + 1])
    p.drawLine(pts[-1], pts[0])

    p.end()
    return QIcon(pix)


def kill_icon(size=20, color="#f48771"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    _setup(p, color)

    c = size / 2.0
    a = size * 0.32
    p.drawLine(QPointF(c - a, c - a), QPointF(c + a, c + a))
    p.drawLine(QPointF(c + a, c - a), QPointF(c - a, c + a))

    p.end()
    return QIcon(pix)
