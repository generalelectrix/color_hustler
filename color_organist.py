"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""

import time

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


































