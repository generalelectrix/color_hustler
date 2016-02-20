from .name_registry import register_name

class ColorPort(object):
    """A general-purpose color output from a modulation stream.

    Publishes its existence to a registry of available ports.
    """
    @register_name
    def __init__(self, col_gen):
        self.col_gen = col_gen
        self.color = None

    def update(self):
        self.color = self.col_gen.get()

    def get(self):
        """Play the color organ if the moment is right."""
        return self.color