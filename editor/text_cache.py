import pygame
from OpenGL.GL import (
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    glDrawPixels,
    glWindowPos2d,
)


_CACHE = {}


def _rasterize(text, color, font):
    key = (str(text), id(font), color)
    entry = _CACHE.get(key)
    if entry is None:
        surf = font.render(str(text), True, color)
        entry = (
            pygame.image.tostring(surf, "RGBA", True),
            surf.get_width(),
            surf.get_height(),
        )
        _CACHE[key] = entry
    return entry


def text_width(text, color, font):
    return _rasterize(text, color, font)[1]


def draw(text, x, y, color, font, viewport_h):
    data, w, h = _rasterize(text, color, font)
    glWindowPos2d(int(x), int(viewport_h - y - h))
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
