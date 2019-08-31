"""A player piano for the color organ.

Conversion of a color into a midi event in color organ scheme:
Velocity = intensity
Hue = midi note, use 0 to 127 for maximum expression (still not a lot of colors...)
Saturation: set as a control change before sending the note
"""
from mido import Message

# control mappings
CC_SAT = 11

def unit_float_to_7bit(number):
    """Convert a float on the range [0,1] to an int on the range [0,127]."""
    return min(int(number*128), 127)

class ColorOrganist:
    """Takes a stream of colors and sends them to a LD50 color organ."""
    def __init__(self, ctrl_channel, note_trig, col_gen):
        self.ctrl_channel = ctrl_channel
        self.note_trig = note_trig
        self.col_gen = col_gen

    def play(self, midi_port):
        """Play the color organ if the moment is right."""
        # should this organist play a note?
        if not self.note_trig.trigger():
            return

        color = self.col_gen.get()

        # convert the color to HSV
        col_hsv = color.in_hsv()

        # color organ hue is offset by 0.5 to put red at the center of the keyboard
        note = unit_float_to_7bit((col_hsv.hue_hsv + 0.5) % 1.0)
        velocity = unit_float_to_7bit(col_hsv.val_hsv)
        saturation = unit_float_to_7bit(col_hsv.sat_hsv)

        sat_msg = Message(
            'control_change',
            channel=self.ctrl_channel,
            control=CC_SAT,
            value=saturation)

        on_msg = Message(
            'note_on', channel=self.ctrl_channel, note=note, velocity=velocity)
        off_msg = Message(
            'note_off', channel=self.ctrl_channel, note=note, velocity=velocity)

        midi_port.send(sat_msg)
        midi_port.send(on_msg)
        midi_port.send(off_msg)
