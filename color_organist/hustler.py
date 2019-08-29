"""Show setup for color hustler.

Provides color selection with stochastic variants on each color parameter.
"""
import mido
from .color import ColorGenerator
from .organ import ColorOrganist
from .param_gen import Noise
from .rate import Trigger, Rate
from .show import Show


def initialize(midi_port_name, framerate=60.0):
    midi_port = mido.open_output(midi_port_name)

    show = Show(framerate=framerate, midi_port=midi_port)

    def add_random_source(name, center=0.0):
        generator = Noise(mode=Noise.GAUSSIAN, center=center, width=0.0)
        show.register_entity(generator, name)
        return generator

    # build modulation chains for each color coordinate
    h_gen = add_random_source('hue')
    s_gen = add_random_source('saturation')
    l_gen = add_random_source('lightness', center=0.5)

    # wire these things up to an organist
    color_gen = ColorGenerator(h_gen=h_gen, s_gen=s_gen, v_gen=l_gen)

    note_trig = Trigger(rate=Rate(hz=1.0))
    show.register_entity(note_trig, 'note_trigger')

    organist = ColorOrganist(ctrl_channel=1, note_trig=note_trig, col_gen=color_gen)
    show.organists.add(organist)

    return show


