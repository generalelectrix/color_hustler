"""A player piano for the color organ.

Conversion of a color into a midi event in color organ scheme:
Velocity = intensity
Hue = midi note, use 0 to 127 for maximum expression (still not a lot of colors...)
Saturation: set as a control change before sending the note
"""
import mido

from name_registry import register_name

# control mappings
CC_SAT = 11

# show saving
SHOW_SUFFIX = '.colorg'

class MidiPort(object):
    """Global midi port.

    Implemented as a Singleton to simplify loading saved shows, as the mido
    midi library is implemented using ctypes and these objects cannot be pickled.
    Instead we call the constructor MidiPort() wherever we want to use the global
    port for the show rather than holding on to a reference to it.  Not optimally
    efficient but not an issue thus far.
    """
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
        # convert the color to HSV
        col_hsv = color.in_hsv()

        # color organ hue is offset by 0.5 to put red at the center of the keyboard
        note = unit_float_to_7bit((col_hsv.hue_hsv + 0.5) % 1.0)
        velocity = unit_float_to_7bit(col_hsv.val_hsv)
        saturation = unit_float_to_7bit(col_hsv.sat_hsv)

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

class InvalidBankError(Exception):
    pass


































