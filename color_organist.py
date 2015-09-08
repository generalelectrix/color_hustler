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
        self.port = MidiPort()
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

def test_color_organist_functions_local():

    import time

    p = mido.open_output()

    co = ColorOrgan(p, 0, 1, {'linear': 0, 'all': 1})

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

    # check random color generation
    # full brightness, unform random hue and sat
    h_gen = pgen.UniformRandom(0.5, 0.5, name='hgen')
    s_gen = pgen.UniformRandom(0.5, 0.5, name='sgen')
    b_gen = pgen.Constant(1.0, name='bgen')

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen, name='cgen')

    co.select_bank('linear')

    for _ in xrange(24):
        col = c_gen.get()
        co.send_color(col)
        time.sleep(0.3)

def test_co_functions_process():

    import time

    ports = mido.get_output_names()
    p = mido.open_output(ports[0])

    organ = ColorOrgan('test organ', p, 0, 1, {'linear': 0, 'all': 1}, name='organ')

    #c_gen = nice_color_gen_default(cyan())
    c_gen = test_hue_gen(red())

    def add_to_hue(cgen, mod):
        new_center = pgen.wrap(cgen.h_gen.center + mod, 0.0, 1.0)
        cgen.h_gen.center = new_center

    diffusor = pgen.Diffusor(Rate(period=60.0), name='diffusor')

    mutator_chain = pgen.MutatorZombieHerd(c_gen, name='mut_chain')
    mutator_chain.append(pgen.Twiddler(diffusor, add_to_hue, name='diffusor twiddler'))

    mod_chain = pgen.ModulationChain(mutator_chain, name='mod_chain')

    note_trig = ClockTrigger(Rate(bpm=240.), 'note_trig')

    organist = ColorOrganist(note_trig, mod_chain, name='organist')

    wc = WallClock()
    wc.tick()
    now = wc.time()
    print NameRegistry()
    while True:
        organist.play(organ)
        time.sleep(0.02)
        wc.tick()
        if wc.time() > now + 20.0:
            break

class InvalidBankError(Exception):
    pass


































