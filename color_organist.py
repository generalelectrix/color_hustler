"""A player piano for the color organ.

Necessary elements:

Conversion of a color into a midi event in color organ scheme.

Velocity = intensity
Hue = midi note
Use 0 to 127 for maximum expression (still not a lot of colors...)

Saturation: set as a control change before sending the note
"""

import logging
import multiprocessing
import traceback
from threading import Thread
from Queue import Empty
import multiprocessing as mp
from multiprocessing import Process

from contextlib import contextmanager

import mido

import param_gen as pgen
from color import Color, HSBColorGenerator
from color import red, green, blue, cyan, magenta, yellow
from rate import Rate, ClockTrigger, WallClock
from name_registry import *

# control mappings
CC_SAT = 11

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
    @named
    def __init__(self, name, port, ctrl_channel, bank_channel, banks=None):
        self.name = name
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

class ColorOrganist(object):
    """Class which uses a color stream to play a color organ."""
    @named
    def __init__(self, note_trig, col_gen):
        self.note_trig = note_trig
        self.col_gen = col_gen

    def play(self, organ):
        """Play a color organ if the moment is right."""
        # should this organist play a note?
        if self.note_trig.trigger():
            organ.send_color(self.col_gen.get())

def nice_color_gen_default(start_color):
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
    return HSBColorGenerator(h_gen, s_gen, b_gen)

def test_hue_gen(start_color):
    """Return a color generator that produces a constant color."""
    h_gen = pgen.Constant(start_color.hue)
    s_gen = pgen.Constant(1.0)
    b_gen = pgen.Constant(1.0)
    return HSBColorGenerator(h_gen, s_gen, b_gen)

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
    h_gen = pgen.UniformRandom(0.5, 0.5)
    s_gen = pgen.UniformRandom(0.5, 0.5)
    b_gen = pgen.Constant(1.0)

    c_gen = HSBColorGenerator(h_gen, s_gen, b_gen)

    co.select_bank('linear')

    for _ in xrange(24):
        col = c_gen.get()
        co.send_color(col)
        time.sleep(0.3)

def test_co_functions_process():

    import time

    ports = mido.get_output_names()
    p = mido.open_output(ports[0])

    organ = ColorOrgan('test organ', p, 0, 1, {'linear': 0, 'all': 1})

    #c_gen = nice_color_gen_default(cyan())
    c_gen = test_hue_gen(red())

    def add_to_hue(cgen, mod):
        new_center = pgen.wrap(cgen.h_gen.center + mod, 0.0, 1.0)
        cgen.h_gen.center = new_center

    diffusor = pgen.Diffusor(Rate(period=60.0))

    mutator_chain = pgen.MutatorZombieHerd(c_gen)
    mutator_chain.append(pgen.Twiddler(diffusor, add_to_hue))

    mod_chain = pgen.ModulationChain(mutator_chain)

    note_trig = ClockTrigger(Rate(bpm=240.))

    organist = ColorOrganist(note_trig, mod_chain)

    wc = WallClock()
    wc.tick()
    now = wc.time()
    while True:
        organist.play(organ)
        time.sleep(0.02)
        wc.tick()
        if wc.time() > now + 20.0:
            break


class Application(object):
    """Encapsulate the runtime environment and application code."""
    def __init__(self, framerate):
        self.framerate = Rate(hz=framerate)
        self.render_trigger = ClockTrigger(self.framerate, absolute_time=True)
        self.named_entities = {}

        self.organs = []

    def run(self):
        # instance the wall clock and call first tick
        wc = WallClock()
        wc.tick()
        # application loop
        while True:

            if render_trigger.trigger():
                # render this frame to midi

                # command the organs to play
                for organ in organs:
                    organ.play()

                # update the wall clock for the next frame
                wc.tick()

            else:
                while render_trigger.time_until_trig() > 0.0:
                    # if we have time left until render, use it to process events

                    # wait for an event
                    #TODO: implement command parsing
                    # store the command
                    # update the wall clock
                    wc.tick()
                    # apply the command

                    # update the wall clock again
                    wc.tick()

                    # TODO: have the


class InvalidBankError(Exception):
    pass

class RateError(Exception):
    pass

class MidiServiceError(Exception):
    pass

class MidiServiceNotRunning(MidiServiceError):
    pass



if __name__ == '__main__':
    #test_color_organist_functions_local()
    test_co_functions_process()


































