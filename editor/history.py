from editor.constants import UNDO_DEPTH
from editor.objects import Object3D


class History:
    def __init__(self):
        self._stack = []
        self._index = -1

    def clear(self):
        self._stack = []
        self._index = -1

    def push(self, level):
        state = {
            "height": float(level.height),
            "objects": [o.to_dict() for o in level.objects],
        }
        self._stack = self._stack[: self._index + 1]
        self._stack.append(state)
        self._index = len(self._stack) - 1
        while len(self._stack) > UNDO_DEPTH:
            self._stack.pop(0)
            self._index -= 1

    def can_undo(self):
        return self._index > 0

    def can_redo(self):
        return self._index < len(self._stack) - 1

    def undo(self, level):
        if not self.can_undo():
            return False
        self._index -= 1
        self._apply(self._stack[self._index], level)
        return True

    def redo(self, level):
        if not self.can_redo():
            return False
        self._index += 1
        self._apply(self._stack[self._index], level)
        return True

    def _apply(self, state, level):
        level.height = state["height"]
        level.objects = [Object3D.from_dict(d) for d in state["objects"]]
        level._rebuild_pads()
        level.end_pad.position[1] = level.height - 0.5
