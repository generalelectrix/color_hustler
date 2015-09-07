# color organ style HSB color

class Color(object):
    """Roll my own HSB color to match how the color organ works."""
    def __init__(self, hue, saturation, brightness):
        """HSB on unit float intervals."""
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

    def __str__(self):
        return "Color; (h,s,b) = ({},{},{})".format(self.hue, self.saturation, self.brightness)

    def __eq__(self, other):
        if isinstance(other, Color):
            return (self.h == other.h and
                    self.s == other.s and
                    self.b == other.b)

    def __ne__(self, other):
        return not self == other

    @property
    def h(self):
        return self.hue
    @property
    def s(self):
        return self.saturation
    @property
    def b(self):
        return self.brightness

# possibly useful color constants

def red():
    return Color(0.5, 1.0, 1.0)

def green():
    return Color(1.0/6.0, 1.0, 1.0)

def blue():
    return Color(5.0/6.0, 1.0, 1.0)

def cyan():
    return Color(0.0, 1.0, 1.0)

def yellow():
    return Color(1.0/3.0, 1.0, 1.0)

def magenta():
    return Color(2.0/3.0, 1.0, 1.0)

def black():
    return Color(0.0, 0.0, 0.0)

def white():
    return Color(0.0, 0.0, 1.0)


class HSBColorGenerator(object):
    """Random color generation."""

    def __init__(self, h_gen, s_gen, b_gen):
        """Create a new random color generator."""
        self.h_gen = h_gen
        self.s_gen = s_gen
        self.b_gen = b_gen

    def get(self):
        """Get the next random color from this generator."""
        h_val = self.h_gen.get_constrained(0.0, 1.0)
        s_val = self.s_gen.get_constrained(0.0, 1.0)
        b_val = self.b_gen.get_constrained(0.0, 1.0)
        return Color(h_val, s_val, b_val)