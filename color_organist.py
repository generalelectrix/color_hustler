"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""

import time
from random import Random

import mido

# control mappings
CC_SAT = 11

# color organ style HSB color

class Color(object):
    """Roll my own HSB color to match how the color organ works."""
    def __init__(self, hue, saturation, brightness):
        """HSB on unit float intervals."""
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

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

class RandomParameterGenerator(object):
    """Helper class to generate random numbers with useful properties."""

    def __init__(self):
        """Inheriting classes should define their own constructor."""
        raise NotImplementedError("Inheriting classes must define their own constructor.")

    def get(self):
        """"Get the next raw value from this generator.

        Inheriting classes should override this method.
        """
        raise NotImplementedError("Inheriting classes must override this method.")

    def get_constrained(self, min_val=None, max_val=None, fold=True):
        """Get the next value from this generator wrapped to a given interval.

        The behavior of this method differs depending on the value of the fold
        argument.  If fold=True (default), out-of-range values will be iteratively
        folded back into range.  Otherwise, out-of-range values will be clipped.
        """
        val = self.get()
        if fold:
            return fold(val, min_val, max_val)
        else:
            return clamp(val, min_val, max_val)

class UniformRandomParameterGenerator(RandomParameterGenerator):
    """Generate unformly-distributed random numbers."""
    def __init__(self, center, width):
        """Create a new uniform random number generator.

        Will generate random numbers on the interval [center-width, center+width).

        Args:
            center: the centroid of the generated number cloud
            width: the half-width of the generated number cloud
        """
        self.center = center
        self.width = width
        self.gen = Random()

def in_range(value, min_val=None, max_val=None):
    """Determine if a value is in the interval [min_val, max_val).

    (lower bound inclusive, upper bound exclusive).

    Returns the integer 0 if the value is in range, +1 if it is above the max,
    and -1 if it is below the min.
    """
    in_range = 0
    if min_val is not None and value < min_val:
        in_range = -1
    elif max_val is not None and value >= max_val:
        in_range = 1
    return in_range

def clamp(value, min_val=None, max_val=None):
    val_in_range = in_range(value, min_val, max_val)
    if val_in_range == 0:
        return
    elif val_in_range == +1:
        return max_val
    elif val_in_range == -1:
        return min_val

def fold(value, min_val=None, max_val=None):
    """Fold a floating-point value back into a given range."""
    while True:
        val_in_range = in_range(value, min_val, max_val)
        if val_in_range == 0:
            break
        elif val_in_range == 1:
            value = 2*max_val - value
        elif val_in_range == -1:
            value = 2*min_val - value

class HSBColorGenerator(object):
    """Random color generation."""

    def __init__(self):
        """Create a new random color generator."""
        pass

# conversion from unit float to stupid midi 7-bit number

def unit_float_to_7bit(number):
    """Convert a float on the range [0,1] to an int on the range [0,127]."""
    return min(int(number*128), 127)

def note_onoff_pair(channel, note, velocity):
    on = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
    off = mido.Message('note_off', channel=channel, note=note, velocity=velocity)

    return on, off

class ColorOrganist(object):
    """Takes a stream of colors and sends them to a color organ.

    Also knows how to select banks.  Notes are always sent as a on/off pair
    with no sustain period, as that would be more than I want to deal with
    this late at night and this close to the show :)
    """

    def __init__(self, port, ctrl_channel, bank_channel, banks=None):
        self.port = port
        self.ctrl_channel = ctrl_channel
        self.bank_channel = bank_channel
        if banks is None:
            self.banks = {}
        else:
            self.banks = banks

    def send_color(self, color):
        """Send a color message to the color organ."""
        note = unit_float_to_7bit(color.h)
        velocity = unit_float_to_7bit(color.b)
        saturation = unit_float_to_7bit(color.s)

        sat_msg = mido.Message('control_change',
                               channel=self.ctrl_channel,
                               control=CC_SAT,
                               value=saturation)
        on_msg, off_msg = note_onoff_pair(channel=self.ctrl_channel, note=note, velocity=velocity)

        self.port.send(sat_msg)
        self.port.send(on_msg)
        self.port.send(off_msg)

    def select_bank(self, bank):
        """Select a named bank."""
        try:
            bank_note = self.banks[bank]
        except KeyError:
            raise InvalidBankError("{} is not a valid bank.  Valid banks are {}"
                                   .format(bank, self.banks.keys()))
        on, off = note_onoff_pair(channel=self.bank_channel,
                                  note=bank_note,
                                  velocity=127)
        self.port.send(on)
        self.port.send(off)

def test_color_organist_functions():

    p = mido.open_output()

    co = ColorOrganist(p, 0, 1, {'linear': 0, 'all': 1})

    co.select_bank('linear')

    for _ in xrange(8):
        co.send_color(red())
        time.sleep(0.3)

    co.select_bank('all')
    co.send_color(cyan())
    time.sleep(1.0)
    co.send_color(magenta())
    time.sleep(1.0)
    co.send_color(white())


class InvalidBankError(Exception):
    pass



if __name__ == '__main__':
    test_color_organist_functions()


































