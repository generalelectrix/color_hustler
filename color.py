from random import Random

from name_registry import register_name
import param_gen as pgen

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
    @register_name
    def __init__(self, h_gen, s_gen, b_gen):
        """Create a new random color generator."""
        self.h_gen = h_gen
        self.s_gen = s_gen
        self.b_gen = b_gen

    def get(self):
        """Get the next random color from this generator."""
        h_val = self.h_gen.get_constrained(0.0, 1.0, mode='wrap')
        s_val = self.s_gen.get_constrained(0.0, 1.0, mode='fold')
        b_val = self.b_gen.get_constrained(0.0, 1.0, mode='fold')

        return Color(h_val, s_val, b_val)


class ColorSwarm(object):
    """Agglomerate multiple color generators."""
    @register_name
    def __init__(self, col_gens, random=False, seed=None):
        """Create a new ColorSwarm.

        Args:
            col_gens: ([color generator]) A list of color generators to agglomerate.
            random (default=False): pick a generator randomly when get is called.
            seed (optional): a seed for the swarm's internal RNG
        """
        self.random = random
        self.rand_gen = Random()
        if seed is not None:
            self.rand_gen.seed(seed)
        self.gens = col_gens
        self.next = 0

    def get(self):
        """Get a color from the next generator."""
        if self.random:
            gen = self.rand_gen.randint(0, len(self.gens)-1)
            return self.gens[gen].get()
        else:
            # advance to the next generator first in case the number of gens has
            # changed since the last call.
            self.next = (self.next + 1) % len(self.gens)
            col = self.gens[self.next].get()
            return col

def nice_color_gen_default(start_color, name=None):
    """Instance an aesthetically pleasing color generator.

    start_color is an optional color to start the generator with.  At the moment,
    this just sets the initial center of the hue generator.

    Hue is driven by a gaussian with width of 0.1.
    Saturation is driven by a gaussian centered at 1.0 with width 0.2.
    Brightness is driven by a gaussian centered at 1.0 with width 0.2.
    """
    h_gen = pgen.GaussianRandom(start_color.hue, 0.1)
    s_gen = pgen.GaussianRandom(1.0, 0.2)
    b_gen = pgen.GaussianRandom(1.0, 0.2)
    return HSBColorGenerator(h_gen, s_gen, b_gen, name=name)

def test_hue_gen(start_color, name=None):
    """Return a color generator that produces a constant color."""
    h_gen = pgen.Constant(start_color.hue)
    s_gen = pgen.Constant(1.0)
    b_gen = pgen.Constant(1.0)
    return HSBColorGenerator(h_gen, s_gen, b_gen, name=name)







