from OpenGL.GL import (
    GL_LINE_LOOP,
    GL_LINES,
    GL_QUADS,
    glBegin,
    glColor4f,
    glEnd,
    glLineWidth,
    glVertex2f,
)

from editor.constants import (
    BTN_ACTIVE,
    BTN_BADGE,
    BTN_BG,
    BTN_BORDER,
    BTN_HOVER,
    TXT_DIM,
    TXT_MAIN,
    TXT_WHITE,
    UI_TOOLTIP,
    UI_TOOLTIP_BD,
)
from editor.text_cache import draw as draw_text_impl
from editor.text_cache import text_width


def _gl_color(c, alpha=1.0):
    if c is None:
        return
    if len(c) >= 4:
        glColor4f(c[0], c[1], c[2], c[3])
    else:
        glColor4f(c[0], c[1], c[2], alpha)


def fill(x, y, w, h, color, border=None, border_w=1.0):
    _gl_color(color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

    if border is not None:
        _gl_color(border)
        glLineWidth(border_w)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + 0.5, y + 0.5)
        glVertex2f(x + w - 0.5, y + 0.5)
        glVertex2f(x + w - 0.5, y + h - 0.5)
        glVertex2f(x + 0.5, y + h - 0.5)
        glEnd()


def hline(x, y, w, color):
    _gl_color(color)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glEnd()


def text(s, x, y, color, font, viewport_h):
    draw_text_impl(s, x, y, color, font, viewport_h)


def hit(x, y, w, h, mx, my):
    return (x <= mx <= x + w) and (y <= my <= y + h)


def button(x, y, w, h, label, viewport_h,
           key=None, active=False, accent=None,
           mouse_x=0, mouse_y=0, font_body=None, font_key=None):
    hover = hit(x, y, w, h, mouse_x, mouse_y)
    if active:
        bg, border, txt = BTN_ACTIVE, BTN_ACTIVE, TXT_WHITE
    else:
        bg = BTN_HOVER if hover else BTN_BG
        border, txt = BTN_BORDER, TXT_MAIN

    fill(x, y, w, h, bg, border)

    if accent is not None and not active:
        fill(x, y, 2.5, h, accent)

    offset = 0
    if key is not None:
        badge_w = 22
        fill(x + 3, y + 3, badge_w, h - 6, BTN_BADGE, BTN_BORDER)
        tw_k = text_width(key, TXT_DIM, font_key)
        text(key, x + 3 + (badge_w - tw_k) // 2,
             y + (h - font_key.get_height()) // 2 + 1,
             TXT_DIM, font_key, viewport_h)
        offset = badge_w + 6

    tw_l = text_width(label, txt, font_body)
    if key is None:
        text(label, x + (w - tw_l) // 2,
             y + (h - font_body.get_height()) // 2,
             txt, font_body, viewport_h)
    else:
        text(label, x + offset + 4,
             y + (h - font_body.get_height()) // 2,
             txt, font_body, viewport_h)


def section(x, y, w, label, viewport_h, font):
    text(label, x + 6, y, (0.62, 0.62, 0.62), font, viewport_h)
    hline(x + 6, y + 15, w - 12, (0.16, 0.16, 0.16, 1.0))


def tooltip(x, y, label, viewport_h, font):
    tw = text_width(label, TXT_WHITE, font)
    pad_x = 8
    pad_y = 5
    w = tw + pad_x * 2
    h = font.get_height() + pad_y * 2
    fill(x, y, w, h, UI_TOOLTIP, UI_TOOLTIP_BD)
    text(label, x + pad_x, y + pad_y, TXT_WHITE, font, viewport_h)
    return w, h
