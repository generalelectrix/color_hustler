"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""

import mido

import param_gen as pgen
from color import Color, HSBColorGenerator
from name_registry import NameRegistry, register_name

# control mappings
CC_SAT = 11

# show saving
SHOW_SUFFIX = '.colorg'

class MidiPort(object):
    """Global midi port.  Implemented as a Singleton."""
    __instance = None
    def __new__(cls, port_name=None):
        """Open a named port."""
        if MidiPort.__instance is None:
            if port_name is not None:
                MidiPort.__instance = mido.open_output(port_name)
            else:
                MidiPort.__instance = mido.open_output()
        return MidiPort.__instance

# conversion from unit float to stupid midi 7-bit number

def unit_float_to_7bit(number):
    """Convert a float on the range [0,1] to an int on the range [0,127]."""
    return min(int(number*128), 127)

def note_onoff_pair(channel, note, velocity):
    on = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
    off = mido.Message('note_off', channel=channel, note=note, velocity=velocity)

    return on, off

class ColorOrgan(object):
    """Takes a stream of colors and sends them to a LD50 color organ.

    Also knows how to select banks.  Notes are always sent as a on/off pair
    with no sustain period, as that would be more than I want to deal with
    this late at night and this close to the show :)
    """
    @register_name
    def __init__(self, name, ctrl_channel, bank_channel, banks=None):
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

        MidiPort().send(sat_msg)
        MidiPort().send(on_msg)
        MidiPort().send(off_msg)

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
        MidiPort().send(on)
        MidiPort().send(off)

class ColorOrganist(object):
    """Class which uses a color stream to play a color organ."""
    @register_name
    def __init__(self, organ, note_trig, col_gen):
        self.organ = organ
        self.note_trig = note_trig
        self.col_gen = col_gen

    def play(self):
        """Play the color organ if the moment is right."""
        # should this organist play a note?
        if self.note_trig.trigger():
            self.organ.send_color(self.col_gen.get())

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

class InvalidBankError(Exception):
    pass


































