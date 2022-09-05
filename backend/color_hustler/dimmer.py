from .color import clamp

class Dimmer:
    """Control profile for a basic 8-bit dimmer channel."""

    def __init__(self, address):
        self.address = address
        self.value = 0.0

    def get_controls(self):
        return [self._set_value]

    def _set_value(self, value):
        self.value = clamp(value, 0.0, 1.0)

    def render(self, buf):
        index = self.address - 1
        val_int = int(abs(self.value) * 256.0)
        buf[index] = min(max(val_int, 0), 255)
