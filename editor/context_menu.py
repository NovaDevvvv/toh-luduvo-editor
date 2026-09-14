from editor.constants import SHAPE_MENU


ITEM_H = 26
MENU_W = 168
PAD_Y = 6


class ContextMenu:
    def __init__(self):
        self.active = False
        self.x = 0
        self.y = 0
        self.items = SHAPE_MENU
        self.world_pos = None

    def open(self, x, y, world_pos):
        self.active = True
        self.x = x
        self.y = y
        self.world_pos = world_pos

    def close(self):
        self.active = False
        self.world_pos = None

    def rect(self):
        h = PAD_Y * 2 + len(self.items) * ITEM_H
        return (self.x, self.y, MENU_W, h)

    def item_rect(self, index):
        return (self.x, self.y + PAD_Y + index * ITEM_H, MENU_W, ITEM_H)

    def hit_test(self, mx, my):
        if not self.active:
            return None
        x, y, w, h = self.rect()
        if not (x <= mx <= x + w and y <= my <= y + h):
            return None
        for i in range(len(self.items)):
            ix, iy, iw, ih = self.item_rect(i)
            if ix <= mx <= ix + iw and iy <= my <= iy + ih:
                return i
        return -1
